"""
This management command creates or updates an organism in the database.
The input arguments are the fields specified in the `Organism` model.
The command should be launched like this:

  python manage.py update_or_create_organism \
--tax_id=9606 --common_name="Human" --scientific_name="Homo sapiens" \
--url_template="http://www.example.com/?gene=<systematic_name>"

Note that "--url_template" is optional. If not specified, it defaults to null.
"""

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from organisms.models import Organism


class Command(BaseCommand):
    help = "Create or update an organism in database."

    def add_arguments(self, parser):
        parser.add_argument('--tax_id', dest='tax_id', type=int, required=True)

        parser.add_argument(
            '--common_name',
            dest='common_name',
            required=True,
            help="Organism common name, e.g. 'Human'"
        )

        parser.add_argument(
            '--scientific_name',
            dest='scientific_name',
            required=True,
            help="Organism scientific/binomial name, e.g. 'Homo sapiens'"
        )

        parser.add_argument(
            '--url_template',
            required=False,
            dest='url_template',
            help="URL template for genes of this organism"
        )

    def handle(self, *args, **options):
        tax_id = options['tax_id']

        # Remove leading and trailing blank characters in "common_name"
        # and "scientific_name
        common_name = options['common_name'].strip()
        scientific_name = options['scientific_name'].strip()
        url_template = options['url_template']
        if url_template:
            url_template = url_template.strip()

        if common_name and scientific_name:
            # A 'slug' is a label for an object in django, which only contains
            # letters, numbers, underscores, and hyphens, thus making it URL-
            # usable.  The slugify method in django takes any string and
            # converts it to this format.  For more information, see:
            # http://stackoverflow.com/questions/427102/what-is-a-slug-in-django
            slug = slugify(scientific_name)

            obj, created = Organism.objects.update_or_create(
                taxonomy_id=tax_id,
                defaults = {
                    'common_name': common_name,
                    'scientific_name': scientific_name,
                    'slug': slug,
                    'url_template': url_template
                }
            )

            action = "created" if created else "updated"

            self.stdout.write(
                self.style.SUCCESS(f"Organism {action} successfully")
            )
        else:
            raise CommandError("Failed to update or create organism")
