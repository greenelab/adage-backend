from rest_framework import serializers
from .models import (
    Experiment, MLModel, Sample, SampleAnnotation, Signature, Activity, Edge,
    ParticipationType, Participation,
)

class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'


class ExperimentSerializer(serializers.ModelSerializer):
    """
    Experiment serializer excludes `samples_info` field but includes an
    extra `samples` field with sample IDs and sample names.
    """

    samples = serializers.SerializerMethodField()

    # This field is only populated when `autocomplete` parameter is in the URL
    max_similarity_field = serializers.CharField(required=False)

    class Meta:
        model = Experiment
        fields = (
            'id', 'accession', 'name', 'description',
            'samples', 'max_similarity_field'
        )

    def get_samples(self, record):
        """
        Collect sample IDs and names dynamically and save them in a dictionary.
        """

        samples_set = record.sample_set.all().order_by('id')
        samples = [s.id for s in samples_set]
        return samples


class SampleSerializer(serializers.ModelSerializer):
    annotations = serializers.SerializerMethodField()

    def get_annotations(self, record):
        qs = SampleAnnotation.objects.filter(sample=record).values(
            'annotation_type__typename', 'text'
        )
        annotations = dict()
        for sa in qs:
            k, v = sa['annotation_type__typename'], sa['text']
            annotations[k] = v
        return annotations

    class Meta:
        model = Sample
        fields = ('id', 'name', 'ml_data_source', 'annotations', 'experiments')


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        exclude = ['samples']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        exclude = ['id', ]


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = '__all__'


class ParticipationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipationType
        fields = '__all__'


class ParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participation
        fields = '__all__'
