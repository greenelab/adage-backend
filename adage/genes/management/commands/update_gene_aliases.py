# The docstring in this module is written in rst format so that it can be
# collected by sphinx and integrated into django-genes/README.rst file.

"""
   This management command reads an input tab-delimited file whose first column
   is a gene's PAO1 name (aka. systematic name), and second column is this
   gene's alias (such as PA14 name for Pseudomonas). The latter will be added
   to "aliases" field in the database `gene` table.

   The command requires a positional argument: the input filename. It should be
   invoked like this:
      python manage.py add_gene_alias pao1_to_pa14.tsv
"""


from django.core.management.base import BaseCommand, CommandError
from genes.models import Gene


class Command(BaseCommand):
    help = (
        'Read input tsv file that maps PAO1 genes to their aliases, which will '
        'be added in the database `gene` table as aliases.'
    )

    def add_arguments(self, parser):
        parser.add_argument('alias_file', type=open)

    def handle(self, *args, **options):
        try:
            alias_fh = options['alias_file']
            self.import_aliases(alias_fh)
            self.stdout.write(
                self.style.SUCCESS('Gene aliases imported successfully')
            )
        except Exception as e:
            raise CommandError('Failed to import gene aliases: %s' % e)

    def import_aliases(self, file_handle):
        line_num = 0
        for line in file_handle:
            line_num += 1
            line = line.strip()
            # Skip blank lines or the ones that start with '#'
            if line.startswith('#') or len(line) == 0:
                continue

            tokens = line.split('\t')
            if len(tokens) != 2:
                raise Exception(
                    "Error on line #%d: need two fields but %d is found".format(
                        line_num, len(tokens)
                    )
                )

            pao1_name, pa14_name = tokens[0].strip(), tokens[1].strip()
            try:
                gene = Gene.objects.get(systematic_name=pao1_name)
            except Gene.DoesNotExist:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Line #{line_num} ignored: {pao1_name} not found in database"
                    )
                )
            except Gene.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Line #{line_num} ignored: {pao1_name} matches multiple genes in database"
                    )
                )
            else:
                original_aliases = gene.aliases.strip()
                if len(original_aliases) == 0:
                    alias_list = []
                else:
                    alias_list = original_aliases.split(' ')

                if pa14_name not in alias_list:
                    alias_list.append(pa14_name)
                    gene.aliases = ' '.join(alias_list)
                    gene.save()
