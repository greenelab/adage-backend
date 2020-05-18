"""
This management command collects information of samples that are
associated with each experiment and combines them into a string, which is
then set as the value of `samples_info` field in `Experiment` model. This
field will be used for full text search in `Experiment` API. The samples
information includes:
  * sample name and ml_data_source
  * annotation values associated with each sample

Note: This command should be run ONLY AFTER `Experiment`, `Sample` and
`SampleAnnotation` tables have been populated completely.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from analyze.models import Experiment, Sample, SampleAnnotation


class Command(BaseCommand):
    help = "Set samples_info in each experiment."

    def handle(self, **options):
        try:
            set_samples_info()
            self.stdout.write(
                self.style.SUCCESS("samples_info set successfully")
            )
        except Exception as e:
            raise CommandError("Failed to set samples_info: \n%s" % e)


def get_all_samples_info():
    """
    Returns a dictionary whose key is a sample's ID, and the corresponding
    value is a string of this sample's info.
    """

    all_samples_info = dict()
    for sample in Sample.objects.all():
        sample_info = list()
        sample_info.append(sample.name)
        if sample.ml_data_source:
            sample_info.append(sample.ml_data_source)

        for annotation in SampleAnnotation.objects.filter(sample=sample):
            if annotation.text:
                sample_info.append(annotation.text)
        all_samples_info[sample.id] = "\n".join(sample_info)

    return all_samples_info


def set_samples_info():
    """Update `samples_info` field in each experiment."""

    all_samples_info = get_all_samples_info()
    experiment_qs = Experiment.objects.all()
    with transaction.atomic():
        for experiment in experiment_qs:
            samples = experiment_qs.filter(pk=experiment).values('sample')
            samples_info = ""
            for s in samples:
                sample_id = s['sample']
                samples_info += all_samples_info[sample_id] + "\n"
            experiment.samples_info = samples_info
            experiment.save()
