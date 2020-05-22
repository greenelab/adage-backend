from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):
    dependencies = [('genes', '0001_initial')]

    operations = [
        TrigramExtension(),
    ]
