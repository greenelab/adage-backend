"""
Read an input gene-gene network file and populate the "Edge" table in database.
A valid input file must be tab-delimited, and each line must include 4 columns:

  (1) Systematic name of "from" gene;
  (2) Systematic name of "to" gene;
  (3) Weight of correlation between "from" and "to" genes;
  (4) Sign of the weight (either "+" or "-").

The first line will be ignored as it only has column names.
Here is an example of the input gene-gene network file in this repo:
  data/gene_gene_network_cutoff_0.2.txt.gz

The command requires two arguments:
  (1) filename: name of input gene-gene network file;
  (2) ml_model: title of machine learning model for gene-gene network

For example, to import the gene-gene network in an input file "eADAGE.txt"
whose machine leaning model is "Ensemble ADAGE 300", we will type:
  python manage.py import_gene_network \
--filename=eADAGE.txt --ml_model="Ensemble ADAGE 300"

IMPORTANT:
Before running this command, please make sure that the machine learning model
whose title is `ml_model` already exists in the database.  If it doesn't, use
`create_or_update_ml_model.py` command to create it in the database.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from genes.models import Gene
from analyses.models import MLModel, Edge

NUM_COLUMNS = 4
BULK_SIZE = 2000


class Command(BaseCommand):
    help = ("Imports gene-gene network data into the `Edge` table in database.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename', dest='filename', type=open, required=True
        )
        parser.add_argument(
            '--ml_model', dest='ml_model', type=str, required=True
        )

    def handle(self, **options):
        try:
            import_network(options['filename'], options['ml_model'])
            self.stdout.write(
                self.style.SUCCESS("Gene-gene network data imported successfully")
            )
        except Exception as e:
            raise CommandError("Failed to import gene-gene network data: %s" % e)


def import_network(file_handle, ml_model_title):
    """
    Import gene-gene network data in the database.
    First validate input ml_model_title, then read each valid data line in the
    input file into the database.
    The whole reading/importing process is enclosed in a transaction context
    manager so that any exception raised inside the manager will terminate the
    transaction and roll back the database.
    """

    # Raise an exception if ml_model_title does not exist in the database.
    try:
        ml_model = MLModel.objects.get(title=ml_model_title)
    except MLModel.DoesNotExist:
        raise Exception("ml_model (%s) not found in the database" % ml_model_title)

    # Enclose reading/importing process in a transaction.
    with transaction.atomic():
        check_and_import(file_handle, ml_model)


def check_and_import(file_handle, ml_model):
    """
    Read valid data lines into the database.
    An exception will be raised when error is detected.
    """

    # If the database already includes record(s) of the same ml_model,
    # check the "unique_together" constraint.
    check_unique = Edge.objects.filter(mlmodel=ml_model).exists()

    gene_pairs_in_file = set()
    cached_genes = dict()
    records = []
    for line_num, line in enumerate(file_handle, start=1):
        # Skip the first line, which includes column names only.
        if line_num == 1:
            continue

        # Check the number of columns in the line.
        tokens = line.rstrip('\r\n').split('\t')
        if len(tokens) != NUM_COLUMNS:
            raise Exception(
                "Input file line #%d: number of fields is not %d" %
                (line_num, NUM_COLUMNS)
            )

        # Check whether the gene in column #1 is identical to the gene
        # in column #2.
        if tokens[0] == tokens[1]:
            raise Exception(
                "Input file line #%d: identical genes in columns #1 and #2" %
                line_num
            )

        # Check whether we can convert the combination of column #4 and
        # #3 to a floating point value.
        try:
            weight = float(tokens[3] + tokens[2])
        except ValueError:
            raise Exception(
                "Input file line #%d: weight (%s) not floating type" %
                (line_num, tokens[3] + tokens[2])
            )

        # Check whether the converted floating point value is in the range
        # of [-1.0, 1.0].
        if weight < -1.0 or weight > 1.0:
            raise Exception(
                "Input file line #%d: weight (%s) out of range of -1.0~1.0" %
                (line_num, tokens[3] + tokens[2])
            )

        # Skip the line if the weight is less than cutoff.
        if abs(weight) < ml_model.g2g_edge_cutoff:
            continue

        # Check whether the pair of (column #1, column #2) is duplicate
        # in the file.
        pair01 = tokens[0] + '\t' + tokens[1]
        if pair01 in gene_pairs_in_file:
            raise Exception(
                "Input file line #%d: duplicate pair of genes (%s, %s)" %
                (line_num, tokens[0], tokens[1])
            )
        # If the edges in ml_model are not directed, also check whether
        # the pair of (column #2, column #1) is duplicate in the file.
        if not ml_model.directed_g2g_edge:
            pair10 = tokens[1] + '\t' + tokens[0]
            if pair10 in gene_pairs_in_file:
                raise Exception(
                    "Input file line #%d: duplicate pair of genes (%s, %s)" %
                    (line_num, tokens[1], tokens[0])
                )

        # Keep track of all pairs of (column #1, column #2) that we have
        # processed so that we can check the duplicate in the file later.
        gene_pairs_in_file.add(pair01)

        # If tokens[0] does not match one and only one gene's
        # systematic_name in the database, skip the line.
        try:
            gene1 = find_gene(tokens[0], cached_genes)
        except Exception as e:
            logging.warning("Input file line #%d skipped: %s", line_num, e)
            continue

        # If tokens[1] does not match one and only one gene's
        # systematic_name in the database, skip the line.
        try:
            gene2 = find_gene(tokens[1], cached_genes)
        except Exception as e:
            logging.warning("Input file line #%d skipped: %s", line_num, e)
            continue

        # Check whether the triplet (ml_model, gene1, gene2) is unique.
        if check_unique and not unique_together(ml_model, gene1, gene2):
            raise Exception(
                "Input file line #%d: (%s, %s, %s) not unique in database"
                % (line_num, tokens[0], tokens[1], ml_model.title)
            )

        # Save the valid data into batch.
        records.append(
            Edge(mlmodel=ml_model, gene1=gene1, gene2=gene2, weight=weight)
        )
        if len(records) == BULK_SIZE:  # dump bulk records into database
            Edge.objects.bulk_create(records)
            records = []

    # Don't forget the last bulk:
    if len(records) > 0:
        Edge.objects.bulk_create(records)
        records = []


def find_gene(systematic_name, cached_genes):
    """
    Return the gene in database whose systematic_name matches input
    "systematic_name".  An exception will be raised if no gene is found
    or multiple genes exist in the database.
    """

    if systematic_name in cached_genes:
        return cached_genes[systematic_name]

    try:
        gene = Gene.objects.get(systematic_name=systematic_name)
    except Gene.DoesNotExist:
        raise Exception(
            "gene systematic name (%s) not found in database" % systematic_name
        )
    except Gene.MultipleObjectsReturned:
        raise Exception(
            "gene systematic name (%s) matches multiple records in database"
            % systematic_name
        )

    cached_genes[systematic_name] = gene
    return gene


def unique_together(ml_model, gene1, gene2):
    """
    Check whether the triplet of (ml_model, gene1, gene2) already exists
    in the database.  If ml_model has directed gene-gene edge, check the
    triplet of (ml_model, gene2, gene1) as well.
    Although this "unique together" constraint has been enforced at database
    level, it is still checked explicitly here so that the number of invalid
    line in input file will be reported.
    """

    try:
        Edge.objects.get(mlmodel=ml_model, gene1=gene1, gene2=gene2)
        return False
    except Edge.DoesNotExist:
        if ml_model.directed_g2g_edge:  # check is done if edge is directed.
            return True

    try:
        Edge.objects.get(mlmodel=ml_model, gene1=gene2, gene2=gene1)
        return False
    except Edge.DoesNotExist:
        return True
