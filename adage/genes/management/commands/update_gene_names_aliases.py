# The docstring in this module is written in rst format so that it can be
# collected by sphinx and integrated into django-genes/README.rst file.

"""
   This management command reads an input tab-delimited file whose column #1 is
   a gene's PAO1 name (aka. systematic_name), and column #2 is the gene's name
   (aka. standard_name), and column #3 is a list of aliases (including PA14 name
   for Pseudomonas) delimited by a space character.

   The command requires a positional argument: the input filename. It should be
   invoked like this:
      python manage.py update_gene_names_aliases <path>/updated_genes.tsv
"""


from django.core.management.base import BaseCommand, CommandError
from organisms.models import Organism
from genes.models import Gene

PSEUDOMONAS_ID = 208964

class Command(BaseCommand):
    help = ('Read input tsv file that includes updated gene names and aliases')

    def add_arguments(self, parser):
        parser.add_argument('gene_file', type=open)

    def handle(self, *args, **options):
        try:
            fh = options['gene_file']
            self.update_genes(fh)
            self.stdout.write(
                self.style.SUCCESS('Genes updated successfully')
            )
        except Exception as e:
            raise CommandError('Failed to update genes: %s' % e)

    def update_genes(self, file_handle):
        organism = Organism.objects.get(taxonomy_id=PSEUDOMONAS_ID)
        line_num = 0
        for line in file_handle:
            line_num += 1
            line = line.strip('\n')
            # Skip blank lines or the ones that start with '#'
            if line.startswith('#') or len(line) == 0:
                continue

            tokens = line.split('\t')
            if len(tokens) != 3:
                raise Exception(
                    "Line #%d: need three fields but %d is found" % (line_num, len(tokens))
                )

            pao1_name = tokens[0].strip()
            gene_name = tokens[1].strip()
            aliases = tokens[2].strip()
            try:
                gene = Gene.objects.get(systematic_name=pao1_name)
            except Gene.DoesNotExist:
                Gene.objects.create(
                    systematic_name=pao1_name,
                    standard_name=gene_name,
                    aliases=aliases,
                    organism=organism
                )
            except Gene.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Line #{line_num} ignored: {pao1_name} matches multiple genes in database"
                    )
                )
            else:
                if gene_name:
                    gene.standard_name = gene_name
                if aliases:
                    gene.aliases = aliases
                gene.save()
