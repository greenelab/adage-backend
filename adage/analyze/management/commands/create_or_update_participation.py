"""
This management command uploads an input signature-gene network file to
the "Participation" table in the database.  The input file must be
tab-delimited.  Here is an example file:
  <repo_dir>/data/signature_gene_participation.tsv

The command requires three arguments:
  (1) participation_file: the name of input signature-gene participation file;
  (2) ml_model: ML model of the signatures in participation_file;
  (3) participation_type: type of participation of genes in signatures.

For example, to upload the input file "signature_gene_participation.tsv"
whose machine learning model is "Ensemble ADAGE 300" and participation
type is "High weight genes", we will type:
  python manage.py create_or_update_participation \
/path/of/signature_gene_participation.tsv \
"Ensemble ADAGE 300" \
"High-weight genes"

IMPORTANT: Before running this command, please make sure that:
  (1) ml_model already exists in the database. If it doesn't, you can use
      the management command "add_ml_model.py" to add it to the database.
  (2) participation_type already exists in the database. If it doesn't,
      you can use the management command "create_or_update_participation_type.py"
      to add it to the database.
"""

import statistics
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from genes.models import Gene
from analyze.models import MLModel, Signature, Participation, ParticipationType


class Command(BaseCommand):
    help = "Load signature-gene participation data into database"

    def add_arguments(self, parser):
        parser.add_argument('participation_file', type=open)
        parser.add_argument('ml_model', type=str)
        parser.add_argument('participation_type', type=str)

    def handle(self, **options):
        try:
            create_or_update_participation(
                options['participation_file'],
                options['ml_model'],
                options['participation_type']
            )
            self.stdout.write(
                self.style.SUCCESS("Signature-gene participations updated")
            )
        except Exception as e:
            raise CommandError(
                f"Failed to import signature-gene participation data: {e}"
            )


def create_or_update_participation(file_handle, ml_model, participation_type):
    """
    This function creates or updates `weight` field in participation table.
    It first validates ml_model and participation_type, then reads each line
    in file_handle into the database.  The whole process is enclosed by a
    transaction context manager so that any exception raised due to errors
    detected in file_handle will terminate the transaction and roll back the
    database.
    """

    # Validate ml_model
    try:
        ml_model = MLModel.objects.get(title=ml_model)
    except MLModel.DoesNotExist:
        raise Exception(
            f"Machine learning model not found in database: {ml_model}"
        )

    # Validate participation_type
    try:
        participation_type = ParticipationType.objects.get(
            name=participation_type
        )
    except ParticipationType.DoesNotExist:
        raise Exception(
            f"Participation type not found in database: {participation_type}"
        )

    # Read file_handle and collect heavy genes
    weight_matrix = get_weight_matrix(file_handle)
    heavy_genes = find_heavy_genes(weight_matrix)

    # Enclose reading/importing process in a transaction.
    with transaction.atomic():
        update_db(ml_model, participation_type, heavy_genes)


def get_weight_matrix(file_handle):
    """
    Read each line in file_handle and return the weight matrix as a dict,
    in which each key is the original node name, and each value is a nested
    dict, whose keys are gene systematic names, and values are weights.
    """

    weight_matrix = dict()
    line_num = 0
    for line in file_handle:
        line_num += 1
        tokens = line.strip().split('\t')

        # The first line includes node names only
        if line_num == 1:
            num_columns = len(tokens)
            nodes = tokens[1:]
            for idx, node_name in enumerate(nodes):
                weight_matrix[node_name] = dict()
        else:  # read data lines
            # Validate the number of columns in each line
            if num_columns != len(tokens):
                raise Exception(
                    f"Error on line {line_num}: {len(tokens)} columns found"
                )

            gene_name = tokens[0]
            weights = [float(x) for x in tokens[1:]]
            for idx, w in enumerate(weights):
                node_name = nodes[idx]
                weight_matrix[node_name][gene_name] = w

    return weight_matrix


def find_heavy_genes(weight_matrix):
    """
    Return the heavy genes based on input weight_matrix. The return value
    is a dict, in which each key is a positive or nagative sigature name,
    and each value is a nested dict, whose keys are heavy genes' systematic
    names, and values are corresponding weights.
    """

    heavy_genes = dict()
    for node_name, genes_weights in weight_matrix.items():
        weights = genes_weights.values()

        mean = statistics.mean(weights)
        std_dev = statistics.stdev(weights)

        pos_sig_name = node_name + "pos"
        neg_sig_name = node_name + "neg"

        heavy_genes[pos_sig_name] = dict()
        heavy_genes[neg_sig_name] = dict()

        for g, w in genes_weights.items():
            if w > mean + 2.5 * std_dev:
                heavy_genes[pos_sig_name][g] = w
            elif w < mean - 2.5 * std_dev:
                heavy_genes[neg_sig_name][g] = w

    return heavy_genes


def update_db(ml_model, participation_type, heavy_genes):
    """
    Update database based on heavy_genes.  An exception will be raised
    if any error is detected.
    """

    for sig_name, genes_weights in heavy_genes.items():
        try:
            signature = Signature.objects.get(
                name=sig_name,
                mlmodel=ml_model
            )
        except Signature.DoesNotExist:
            raise Exception(f"Signature {sig_name} not found in database")

        for gene_name, weight in genes_weights.items():
            try:
                gene = Gene.objects.get(systematic_name=gene_name)
            # Ensure that one and only one gene is found in database;
            # if not, generate a warning message and skip this gene.
            except Gene.DoesNotExist:
                print(f"Gene '{gene_name}' not found in database")
                continue
            except Gene.MultipleObjectsReturned:
                print(f"Gene '{gene_name}' matching multiple genes in database")
                continue

            Participation.objects.update_or_create(
                signature=signature,
                gene=gene,
                participation_type=participation_type,
                defaults={'weight': weight}
            )
