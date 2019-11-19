from django.test import TestCase
from organisms.models import Organism

class ModelTest(TestCase):
    def test_create(self):
        foo = Organism.objects.create(
            taxonomy_id=123,
            common_name="foo common",
            scientific_name="foo scientific",
            slug="foo-slug"
        )

        bar = Organism.objects.create(
            taxonomy_id=456,
            common_name="bar common",
            scientific_name="bar scientific",
            slug="bar-slug"
        )

        self.assertEqual(Organism.objects.count(), 2)
        self.assertEqual(Organism.objects.first().taxonomy_id, 123)
        self.assertEqual(Organism.objects.last().slug, "bar-slug")
