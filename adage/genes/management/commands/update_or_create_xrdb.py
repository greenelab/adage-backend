# The docstring in this module is written in rst format so that it can be
# collected by sphinx and integrated into django-genes/README.rst file.

"""
   This command adds cross-reference databases for genes. It **must**
   be called for every new cross-reference database to populate the
   gene and cross-reference objects in the database. It requires 2
   arguments:

   * name: the name of the database

   * URL: the URL for that database, with the string '_REPL_' added at the
     end of the URL

   For example, this command adds Ensembl as a cross-reference
   database:

   ::

      python manage.py genes_add_xrdb --name=Ensembl \
--URL=http://www.ensembl.org/Gene/Summary?g=_REPL_

   And this command adds MIM as a cross-reference database:

   ::

      python manage.py genes_add_xrdb --name=MIM \
--URL=http://www.ncbi.nlm.nih.gov/omim/_REPL_
"""

from django.core.management.base import BaseCommand, CommandError
from genes.models import CrossRefDB


class Command(BaseCommand):
    help = ('Add a cross reference database if one with the provided name '
            'does not exist, or update the URL if it does.')

    def add_arguments(self, parser):
        parser.add_argument('--name', dest='name', required=True)
        parser.add_argument('--URL', dest='url', required=True)

    def handle(self, *args, **options):
        name = options.get('name').strip()
        url = options.get('url').strip()
        if name and url:
            obj, created = CrossRefDB.objects.update_or_create(
                name=name,
                defaults={'name': name, 'url': url}
            )
            action = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(f"CrossRefDB record {action} successfully")
            )
        else:
            raise CommandError(
                "Failed to update or create CrossRefDB record due to invalid arguments"
            )
