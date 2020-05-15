#!/usr/bin/env python

"""
This management command reads an input file of gene-sample expression values
and loads the valid data into the database.  It should be invoked like this:

  python manage.py import_gene_sample_expression \
--filename=<expression_filename> --tax_id=<organism_tax_id>

The two required arguments are:
  (1) filename: input file of gene-sample expression values;
  (2) tax_id: taxonomy ID of the organism for the genes in filename.

For example, to load the expression data file "expr.dat" for organism
"Pseudomonas aeruginosa" (whose taxonomy ID is 208964), the command will be:
  python manage.py import_gene_sample_expression --filename="expr.dat" --tax_id=208964

IMPORTANT:
----------
(1) Before running this command, please make sure that the organism whose
taxonomy ID is `tax_id` already exists in the database.  If it doesn't, use the
management command "create_or_update_organism.py" to add it to the database.

(2) If either the data source (columns in row #1 of input file) or the gene's
systematic name (column #1 of each line after the first row) is not found in
the database, a warning message will be generated, and the data in this column
or row will be skipped.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from organisms.models import Organism
from genes.models import Gene
from analyze.models import Sample, ExpressionValue


class Command(BaseCommand):
    help = "Import gene-sample expression values from an input file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename', dest='filename', type=open, required=True
        )
        parser.add_argument(
            '--tax_id', dest='tax_id', type=int, required=True
        )

    def handle(self, **options):
        try:
            import_expression(options['filename'], options['tax_id'])
            self.stdout.write(
                self.style.SUCCESS("gene-sample expression data imported successfully")
            )
        except Exception as e:
            raise CommandError(
                "Error when importing gene-sample expression data: %s" % e
            )


def import_expression(file_handle, tax_id):
    """
    Read input file and load gene-sample expression values into the database.
    """

    # Make sure input tax_id already exists in database.
    try:
        organism = Organism.objects.get(taxonomy_id=tax_id)
    except Organism.DoesNotExist:
        raise Exception(f"Organism tax_id ({tax_id}) not found in database")

    # Enclose reading/importing process in a transaction context manager.
    # Any exception raised inside the manager will terminate the transaction
    # and roll back the database.
    with transaction.atomic():
        samples = []
        for line_num, line in enumerate(file_handle, start=1):
            tokens = line.rstrip('\r\n').split('\t')
            if line_num == 1:
                tokens = tokens[1:]
                read_header(tokens, samples)
            else:
                import_data_line(line_num, tokens, samples, organism)


def read_header(dat_src_tokens, samples):
    """
    Read input tokens on header line and save the corresponding sample
    object into "samples". (Each token will be searched in the database
    using "ml_data_source" field. If a token does not match any sample's
    ml_data_source, put None into "samples".)

    An exception will be raised if any of the following errors are detected:
      * Sample token is blank (null or consists of space characters only);
      * Sample token is duplicate;
    """

    token_set = set()
    for col_num, data_source in enumerate(dat_src_tokens, start=2):
        if not data_source or data_source.isspace():
            raise Exception(
                "Input file line #1 column #%d: blank data_source" % col_num
            )
        elif data_source in token_set:
            raise Exception(
                "Input file line #1 column #%d: duplicate data source (%s)" %
                (col_num, data_source)
            )
        else:
            try:
                token_set.add(data_source)
                sample = Sample.objects.get(ml_data_source=data_source)
                samples.append(sample)
            except Sample.DoesNotExist:
                samples.append(None)
                logging.warning(
                    "Input file line #1: data_source in column #%d not found "
                    "in the database: %s" % (col_num, data_source)
                )


def import_data_line(line_num, tokens, samples, organism):
    """
    Function that imports numerical values in input tokens into the database.
    An exception will be raised if any of the following errors are detected:
      * The number of columns on this line is not equal to the number of
        samples plus 1.
      * The gene's "systematic_name" field (column #1) is blank;
      * Data field (from column #2 to the end) can not be converted into a
        float type.
    """

    if len(tokens) != len(samples) + 1:
        raise Exception(
            "Input file line #%d: Incorrect number of columns (%d)" %
            (line_num, len(tokens))
        )

    gene_name = tokens[0]
    if not gene_name or gene_name.isspace():
        raise Exception(
            "Input file line #%d: gene name (column #1) is blank" % line_num
        )

    try:
        gene = Gene.objects.get(systematic_name=gene_name, organism=organism)
    except Gene.MultipleObjectsReturned:
        raise Exception(
            "Input file line #%d: gene name %s (column #1) matches multiple "
            "genes in the database" % (line_num, gene_name)
        )
    except Gene.DoesNotExist:
        # If a gene is not found in database, generate a warning message
        # and skip this line.
        logging.warning(
            "Input file line #%d: gene name %s (column #1) not found in "
            "database", line_num, gene_name)
        return

    values = tokens[1:]
    # To speed up the importing process, all expression values on current data
    # line will be saved in "records" and created in bulk at the end.
    records = []
    col_num = 2   # Expression values start from column #2.
    for sample, value in zip(samples, values):
        try:
            float_val = float(value)
        except ValueError:
            raise Exception(
                "Input file line #%d column #%d: expression value %s not numeric"
                % (line_num, col_num, value)
            )
        if sample is not None:
            records.append(
                ExpressionValue(sample=sample, gene=gene, value=float_val)
            )
        col_num += 1

    ExpressionValue.objects.bulk_create(records)  # create records in bulk
