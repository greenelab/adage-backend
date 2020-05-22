# The docstring in this module is written in rst format so that it can be
# collected by Sphinx and integrated into django-genes/README.rst file.

"""
   This command parses gene info file(s) and saves the corresponding
   gene objects into the database. It takes 2 required arguments and 5
   optional arguments:

   * (Required) filename: gene_info file's name;

   * (Required) tax_id: taxonomy ID for organism for which genes are
     being populated;

   * (Optional) gi_tax_id: alternative taxonomy ID for some organisms
     (such as S. cerevisiae), equal to tax_id when not set;

   * (Optional) symbol_col: symbol column in gene info file. Default is 2;

   * (Optional) systematic_col: systematic column in gene info file.
     Default is 3;

   * (Optional) alias_col: the column containing gene aliases. If a hyphen
     '-' or blank space ' ' is passed, symbol_col will be used. Default is 4;

   * (Optional) put_systematic_in_xrdb: name of cross-reference Database
     for which you want to use organism systematic IDs as CrossReference
     IDs. This is useful for Pseudomonas, for example, as systematic IDs
     are saved into "PseudoCAP" cross-reference database.

   The following example shows how to download a gzipped human gene
   info file from NIH FTP server, and populate the database based on
   this file.

   ::

      # Create a temporary data directory:
      mkdir data

      # Download a gzipped human gene info file into data directory:
      wget -P data/ -N \
ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz

      # Unzip downloaded file:
      gunzip -c data/Homo_sapiens.gene_info.gz > data/Homo_sapiens.gene_info

      # Call import_gene_info to populate the Gene table in database:
      python manage.py import_gene_info \
--filename=data/Homo_sapiens.gene_info \
--tax_id=9606 --systematic_col=3 --symbol_col=2
"""

import logging
import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from genes.models import Gene, CrossRefDB, CrossRef
from organisms.models import Organism


class Command(BaseCommand):
    help = 'Import gene_info file into Gene table of the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            dest='filename',
            required=True,
            type=open,
            help="gene_info file (downloaded from NCBI entrez)"
        )
        parser.add_argument(
            '--tax_id',
            dest='tax_id',
            type=int,
            required=True,
            help="taxonomy ID assigned by NCBI to this organism"
        )
        parser.add_argument(
            '--gi_tax_id',
            dest='gi_tax_id',
            type=int,
            help=(
                "To work with cerivisiae's taxonomy id change, use this option; "
                "otherwise tax_id will be used"
            )
        )
        parser.add_argument(
            '--symbol_col',
            dest='symbol_col',
            type=int,
            default=2,
            help="The column containing the symbol id."
        )
        parser.add_argument(
            '--systematic_col',
            dest='systematic_col',
            type=int,
            default=3,
            help=(
                "The column containing the systematic id.  If this is '-' "
                "or blank, the symbol will be used"
            )
        )
        parser.add_argument(
            '--alias_col',
            dest='alias_col',
            type=int,
            default=4,
            help="The column containing gene aliases. Ignored if this is '-' "
        )
        parser.add_argument(
            '--put_systematic_in_xrdb',
            dest='systematic_xrdb',
            help=(
                "Optional: Name of Cross-Reference Database for which you "
                "want to use organism systematic IDs as CrossReference IDs "
                "(Used for Pseudomonas)"
            )
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.import_data(options)
            self.stdout.write(
                self.style.SUCCESS("Gene info data imported successfully")
            )
        except Exception as e:
            raise CommandError("Failed to import gene_info data: %s" % e)

    @staticmethod
    def import_data(options):
        # Load the organism.
        tax_id = options.get('tax_id')
        org = Organism.objects.get(taxonomy_id=tax_id)

        # gene_info file information.
        gene_info_fh = options.get('filename')
        symb_col = options.get('symbol_col')
        syst_col = options.get('systematic_col')
        alias_col = options.get('alias_col')
        systematic_xrdb = options.get('systematic_xrdb')

        # yeast has a taxonomy ID that changed, so when we look at the id from
        # NCBI, we have to use the new one.
        gi_tax_id = options.get('gi_tax_id')
        if gi_tax_id is None:
            gi_tax_id = tax_id

        # Get all genes for this organism from the database.
        entrez_in_db = set(
            Gene.objects.filter(organism=org).values_list(
                'entrez_id', flat=True
            )
        )

        # Get all cross reference pairs that refer to a gene from this
        # organism.
        xr_in_db = set()
        for x in CrossRef.objects.filter(
            gene__entrez_id__in=entrez_in_db
        ).prefetch_related('crossrefdb', 'gene'):
            xr_in_db.add(
                (x.crossrefdb.name, x.xrid, x.gene.entrez_id)
            )

        if tax_id and gene_info_fh:
            # Store all the genes seen thus far so we can remove obsolete
            # entries.
            entrez_seen = set()
            # Store all the crossref pairs seen thus far to avoid duplicates.
            # Cache of cross reference databases, which saves hits to DB.
            xrdb_cache = {}
            # Check to make sure the organism matched so that we don't mass-
            # delete for no reason.
            org_matches = 0
            entrez_found = 0    # Found from before.
            entrez_updated = 0  # Found from before and updated.
            entrez_created = 0  # Didn't exist, added.
            for line in gene_info_fh:
                if line.startswith('#'):  # skip the line that starts with "#"
                    continue

                tokens = line.strip().split('\t')
                if tokens[symb_col] == "NEWENTRY":
                    logging.info("NEWENTRY line skipped")
                    continue;

                if int(tokens[0]) != gi_tax_id:  # From wrong organism, skip.
                    #print("dhu:", tokens[0], gi_tax_id)
                    continue

                org_matches += 1  # Count lines that came from this organism.
                # Grab requested fields from tab delimited file.
                (entrez_id, standard_name, systematic_name, aliases, crossrefs,
                 description, status, chromosome
                ) = (
                    int(tokens[1]), tokens[symb_col], tokens[syst_col],
                    tokens[alias_col].strip(), tokens[5], tokens[8],
                    tokens[9], tokens[6]
                )

                # This column only gets filled in for certain organisms.
                if (not systematic_name) or (systematic_name == '-'):
                    systematic_name = standard_name
                # Gene is actually mitochondrial, change symbol to avoid
                # duplicates (analogous to what GeneCards does).
                if chromosome == "MT":
                    if not systematic_name.startswith('MT'):
                        logging.debug(
                            "Renaming %s to %s, mitochondrial version",
                            systematic_name, "MT-" + systematic_name
                        )
                        systematic_name = "MT-" + systematic_name

                alias_str = ''
                alias_num = 0
                if aliases and aliases != '-':
                    alias_list = aliases.split('|')
                    alias_num = len(alias_list)
                    alias_str = ' '.join(alias_list)

                # Handle cross references.
                xref_tuples = []
                if crossrefs and (crossrefs != '-'):
                    xref_tuples = set()
                    if (systematic_xrdb):
                        xref_tuples.add((systematic_xrdb, systematic_name))

                    xrefs = crossrefs.split('|')
                    for x in xrefs:
                        xref_tuples.add(tuple(x.split(':')))

                xref_num = len(xref_tuples)
                # Arbitrary weight for search results.
                # The principle of weighting is that we think people are more
                # likely to want a gene that occurs in more databases or has
                # more aliases b/c it is better-known.  This helps break
                # ordering ties where gene names are identical.
                weight = 2 * xref_num + alias_num

                # We also assume that people are much more likely to want
                # protein coding genes.  In the long term we could measure
                # actual selections and estimate weight per gene.
                if status == 'protein-coding':
                    weight = weight * 2

                gene_object = None
                entrez_seen.add(entrez_id)
                if entrez_id in entrez_in_db:  # This existed already.
                    logging.debug("Entrez %s existed already.", entrez_id)
                    entrez_found += 1
                    gene_object = Gene.objects.get(entrez_id=entrez_id,
                                                   organism=org)
                    changed = False
                    # The following lines update characteristics that may have
                    # changed.
                    if gene_object.systematic_name != systematic_name:
                        gene_object.systematic_name = systematic_name
                        changed = True
                    if gene_object.standard_name != standard_name:
                        gene_object.standard_name = standard_name
                        changed = True
                    if gene_object.description != description:
                        gene_object.description = description
                        changed = True
                    if gene_object.aliases != alias_str:
                        gene_object.aliases = alias_str
                        changed = True
                    if gene_object.weight != weight:
                        gene_object.weight = weight
                        changed = True
                    # If the gene was marked obsolete but occurs in the
                    # gene_info file, then it's not obsolete.
                    if gene_object.obsolete:
                        gene_object.obsolete = False
                        changed = True
                    if changed:
                        entrez_updated += 1
                        # To save time, only call save() if something has been
                        # changed.
                        gene_object.save()

                else:  # New entrez_id observed.
                    logging.debug(
                        "Entrez %s did not exist and will be created.", entrez_id
                    )
                    gene_object = Gene(entrez_id=entrez_id, organism=org,
                                       systematic_name=systematic_name,
                                       standard_name=standard_name,
                                       description=description, obsolete=False,
                                       weight=weight)
                    gene_object.save()
                    entrez_created += 1

                # Add crossreferences.
                for xref_tuple in xref_tuples:
                    try:
                        xrdb = xrdb_cache[xref_tuple[0]]
                    except KeyError:
                        try:
                            xrdb = CrossRefDB.objects.get(name=xref_tuple[0])
                        except CrossRefDB.DoesNotExist:
                            xrdb = None
                        xrdb_cache[xref_tuple[0]] = xrdb
                    if xrdb is None:  # Don't understand crossrefdb, skip.
                        logging.warning(
                            "crossrefdb (%s) not in database for pair %s.",
                            xref_tuple[0], xref_tuple
                        )
                        continue
                    logging.debug('Found crossreference pair %s.', xref_tuple)
                    # If the record doesn't exist in database, create it.
                    if not (xref_tuple[0], xref_tuple[1],
                            entrez_id) in xr_in_db:
                        xr_obj = CrossRef(
                            crossrefdb=xrdb, xrid=xref_tuple[1], gene=gene_object
                        )
                        xr_obj.save()

            # Update "obsolete" attribute for entrez records that are in the
            # database but not in input file.
            for id in entrez_in_db:
                if id not in entrez_seen:
                    gene_object = Gene.objects.get(entrez_id=id, organism=org)
                    if not gene_object.obsolete:
                        gene_object.obsolete = True
                        gene_object.save()

            logging.info(
                "%s entrez identifiers existed in the database and were found "
                "in the new gene_info file",
                entrez_found
            )
            logging.info(
                "%s entrez identifiers existed in the database and were "
                "changed in the new gene_info file",
                entrez_updated
            )
            logging.info(
                "%s entrez identifiers did not exist and were created in the "
                "new gene_info file",
                entrez_created
            )
            if org_matches < 10:
                raise Exception(
                    'Less than 10 gene records found for this organism. '
                    'Please check the input organism tax_id.'
                )
        else:
            raise Exception("Invalid organism tax_id (%s)" % tax_id)
