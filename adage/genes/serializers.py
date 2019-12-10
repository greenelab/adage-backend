from rest_framework import serializers
from .models import Gene
from django.db.models.fields import FloatField

class GeneSerializer(serializers.ModelSerializer):
    # Extra fields for similarity search
    max_similarity_field = serializers.CharField(default=None)

    class Meta:
        model = Gene
        fields = '__all__'
