from rest_framework import serializers
from .models import Gene
from django.db.models.fields import FloatField

class GeneSerializer(serializers.ModelSerializer):
    # This field is only populated when `autocomplete` parameter is in the URL
    max_similarity_field = serializers.CharField(required=False)

    class Meta:
        model = Gene
        fields = '__all__'
