from django.core.management.base import BaseCommand
from organisms.models import Organism
from tribe_client.utils import pickle_organism_public_genesets


class Command(BaseCommand):
    help = (
        'Loop through all the organisms in the database and pickle all the '
        'publicly available Tribe genesets for each of those organisms.'
    )

    def handle(self, *args, **options):
        for organism in Organism.objects.all():
            try:
                pickle_organism_public_genesets(organism.scientific_name)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Successfully pickled Tribe public genesets for " +
                        "organism " + organism.scientific_name
                    )
                )
            except Exception as e:
                self.stderr.write(
                    "Error when pickling Tribe public genesets for organism " +
                    organism.scientific_name + ": " + str(e)
                )
