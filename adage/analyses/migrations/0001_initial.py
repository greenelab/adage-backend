# Generated by Django 3.0.3 on 2020-05-21 15:13

import analyses.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organisms', '0001_initial'),
        ('genes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='AnnotationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typename', models.CharField(max_length=40, unique=True, validators=[analyses.models.validate_pyname], verbose_name='name for this AnnotationType (usable as a Python identifier)')),
                ('description', models.CharField(blank=True, max_length=140)),
            ],
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accession', models.CharField(max_length=48, unique=True)),
                ('name', models.CharField(max_length=1000)),
                ('description', models.TextField()),
                ('samples_info', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='MLModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=1000, unique=True)),
                ('directed_g2g_edge', models.BooleanField(default=False)),
                ('g2g_edge_cutoff', models.FloatField(default=0.0)),
                ('authors', models.TextField(blank=True, null=True)),
                ('journal', models.CharField(blank=True, max_length=2048, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('affiliations', models.TextField(blank=True, null=True)),
                ('funders', models.TextField(blank=True, null=True)),
                ('description', models.CharField(blank=True, max_length=2048, null=True)),
                ('url', models.CharField(blank=True, max_length=2048, null=True)),
                ('references', models.TextField(blank=True, null=True)),
                ('license', models.CharField(blank=True, max_length=2048, null=True)),
                ('organism', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organisms.Organism')),
            ],
        ),
        migrations.CreateModel(
            name='ParticipationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='sample name')),
                ('ml_data_source', models.CharField(blank=True, max_length=120, null=True, unique=True, verbose_name='Machine Learning data used for modeling, e.g. CEL file')),
                ('experiments', models.ManyToManyField(to='analyses.Experiment')),
            ],
        ),
        migrations.CreateModel(
            name='Signature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('mlmodel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.MLModel')),
                ('samples', models.ManyToManyField(through='analyses.Activity', to='analyses.Sample')),
            ],
            options={
                'unique_together': {('name', 'mlmodel')},
            },
        ),
        migrations.AddField(
            model_name='activity',
            name='sample',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.Sample'),
        ),
        migrations.AddField(
            model_name='activity',
            name='signature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.Signature'),
        ),
        migrations.CreateModel(
            name='SampleAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True, verbose_name='annotation text')),
                ('annotation_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.AnnotationType')),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analyses.Sample')),
            ],
            options={
                'unique_together': {('annotation_type', 'sample')},
            },
        ),
        migrations.CreateModel(
            name='Participation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField(null=True)),
                ('gene', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='genes.Gene')),
                ('participation_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.ParticipationType')),
                ('signature', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.Signature')),
            ],
            options={
                'unique_together': {('signature', 'gene', 'participation_type')},
            },
        ),
        migrations.CreateModel(
            name='ExpressionValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('gene', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='genes.Gene')),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.Sample')),
            ],
            options={
                'unique_together': {('sample', 'gene')},
            },
        ),
        migrations.CreateModel(
            name='Edge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField()),
                ('gene1', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gene1', to='genes.Gene')),
                ('gene2', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gene2', to='genes.Gene')),
                ('mlmodel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='analyses.MLModel')),
            ],
            options={
                'unique_together': {('mlmodel', 'gene1', 'gene2')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='activity',
            unique_together={('sample', 'signature')},
        ),
    ]
