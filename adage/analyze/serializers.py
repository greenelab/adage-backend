from rest_framework import serializers
from .models import (
    Experiment, MLModel, Sample, SampleAnnotation, Signature, Edge,
    ParticipationType, Participation,
)


class ExperimentSerializer(serializers.ModelSerializer):
    """Experiment serializer that excludes `samples_info` field but
    includes an extra `samples` field.
    """

    class Meta:
        model = Experiment
        fields = ('accession', 'name', 'description', 'samples')

    samples = serializers.SerializerMethodField()

    def get_samples(self, record):
        """Collect samples dynamically and save them in a dictionary.
        `sample_info` field has the same information but doesn't include
        field names, so it is not user-friendly.
        """

        samples_qs = Experiment.objects.filter(pk=record).values(
            'sample__id', 'sample__name', 'sample__ml_data_source',
            'sample__sampleannotation__annotation_type__typename',
            'sample__sampleannotation__text'
        ).order_by('sample__id')

        samples = list()
        previous_id = None
        current_sample = None
        for s in samples_qs:
            id = s['sample__id']
            name = s['sample__name']
            annotation_type = s['sample__sampleannotation__annotation_type__typename']
            annotation_value = s['sample__sampleannotation__text']
            if id != previous_id:
                if current_sample:
                    samples.append(current_sample)
                ml_data_source = s['sample__ml_data_source']
                current_sample = {
                    'id': id,
                    'name': name,
                    'ml_data_source': ml_data_source,
                    'annotations': {annotation_type: annotation_value}
                }
            else:
                current_sample['annotations'][annotation_type] = annotation_value
            previous_id = id

        samples.append(current_sample)
        return samples


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = '__all__'


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        exclude = ['samples']


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
