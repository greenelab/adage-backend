from django.db import models


class Organism(models.Model):
    taxonomy_id = models.PositiveIntegerField(
        db_index=True, unique=True,
        help_text="Taxonomy ID assigned by NCBI"
    )

    common_name = models.CharField(
        max_length=60, unique=True,
        help_text="Organism common name, e.g. 'Human'"
    )

    scientific_name = models.CharField(
        max_length=60, unique=True,
        help_text="Organism scientific/binomial name, e.g. 'Homo sapiens'"
    )

    # A 'slug' is a label for an object in django, which only contains letters,
    # numbers, underscores, and hyphens, thus making it URL-usable.
    # For more information, see:
    # http://stackoverflow.com/questions/427102/what-is-a-slug-in-django
    slug = models.SlugField(
        unique=True,
        help_text="URL slug created by calling slugify() on scientific_name in"
        " the management command when the organism is added"
    )

    # Optional field: URL template for genes of this organism
    url_template = models.URLField(null=True)

    # To support Python 2, use "python_2_unicode_compatible" decorator. See:
    # https://docs.djangoproject.com/en/1.11/ref/models/instances/#django.db.models.Model.__str__
    def __str__(self):
        return self.scientific_name
