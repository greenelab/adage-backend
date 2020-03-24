from django.db import models


class Organism(models.Model):
    """
    The class 'Organism' is a Django model constructor, which is the blueprint
    for the information that will be stored in the database for each 'organism'
    instance.  Each model in Django corresponds to a table in a database, and
    each field corresponds to a column for that table.  Each Django model
    inherently has a save() method (that can be overwritten and added to),
    which creates an instance of the object in the table and saves the object
    information in the fields.  For more information, see:
    https://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # Fields marked with 'unique=True' must be unique for every entry
    # (organism) or a database exception will be raised.
    # For more information on the types of fields, see:
    # https://docs.djangoproject.com/en/dev/ref/models/fields/
    taxonomy_id = models.PositiveIntegerField(
        db_index=True, unique=True,
        help_text="Taxonomy ID assigned by NCBI")

    common_name = models.CharField(
        max_length=60, unique=True,
        help_text="Organism common name, e.g. 'Human'")

    scientific_name = models.CharField(
        max_length=60, unique=True,
        help_text="Organism scientific/binomial name, e.g. 'Homo sapiens'")

    # A 'slug' is a label for an object in django, which only contains letters,
    # numbers, underscores, and hyphens, thus making it URL-usable.
    # For more information, see:
    # http://stackoverflow.com/questions/427102/what-is-a-slug-in-django
    slug = models.SlugField(
        unique=True,
        help_text="URL slug created by calling slugify() on scientific_name in"
        " the management command when the organism is added")

    # Optional field: URL template for genes of this organism
    url_template = models.URLField(null=True)

    # To support Python 2, use "python_2_unicode_compatible" decorator. See:
    # https://docs.djangoproject.com/en/1.11/ref/models/instances/#django.db.models.Model.__str__
    def __str__(self):
        return self.scientific_name
