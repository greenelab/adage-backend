from rest_framework import serializers
from .models import (
    MLModel,
)


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'
