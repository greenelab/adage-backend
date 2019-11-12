from rest_framework import serializers
from .models import Experiment, MLModel, Sample, Signature


class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = '__all__'


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = '__all__'


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        exclude = ['samples']
