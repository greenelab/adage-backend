"""
Enable `pg_trgm` extension in Postgres.  This migration file is equivalent
to running the following command in psql:
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
"""

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):
    dependencies = [('genes', '0001_initial')]

    operations = [
        TrigramExtension(),
    ]
