# Generated by Django 2.2.5 on 2019-11-22 17:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyze', '0001_squashed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mlmodel',
            old_name='publisher',
            new_name='journal',
        ),
    ]
