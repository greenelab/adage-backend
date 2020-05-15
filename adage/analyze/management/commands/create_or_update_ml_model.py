"""
Create or update the machine learning model that is specified by an
input YAML file.  This management command should be invoked like this:
  python manage.py create_or_update_mlmodel <ml_model_config.yml>
in which `<ml_model_config.yml>` is the input YAML file.

For details of input YAML file's format, see the two examples in this repo:
  * data/simple_ml_model.yml
  * data/complex_ml_model.yml
"""

import yaml
from django.core.management.base import BaseCommand, CommandError
from organisms.models import Organism
from analyze.models import MLModel


class Command(BaseCommand):
    help = "Create or update the machine learning model specified by an YAML file"

    def add_arguments(self, parser):
        parser.add_argument('yml_filename', type=str)

    def handle(self, **options):
        try:
            self.set_ml_model(options['yml_filename'])
        except Exception as e:
            raise CommandError("Failed to set machine learning model: %s" % e)

    def set_ml_model(self, yml_filename):
        with open(yml_filename) as config_file:
            model_config = yaml.full_load(config_file)

        organism_tax_id = model_config.get('organism_tax_id', None)
        title = model_config.get('title', None)

        # Check `organism_tax_id` and `title` fields
        if not organism_tax_id or not title:
            raise Exception(f'`organism_tax_id` or `title` not found in {yml_filename}')
        if not isinstance(organism_tax_id, int):
            raise Exception('`organism_tax_id` not an integer')
        title = title.strip()
        if not title:
            raise Exception('`title` must be a non-empty string')

        # Get organism instance
        try:
            organism = Organism.objects.get(taxonomy_id=organism_tax_id)
        except Organism.DoesNotExist:
            raise Exception(f"organism_tax_id ({organism_tax_id}) not found in the database")

        # Make the keys in `model_config` consistent with the fields in MLModel
        model_config.pop('organism_tax_id')
        model_config['organism'] = organism

        obj, created = MLModel.objects.update_or_create(
            title=title,
            defaults=model_config
        )

        action = "created" if created else "updated"

        self.stdout.write(
            self.style.SUCCESS(f"Machine learning model {action} successfully")
        )
