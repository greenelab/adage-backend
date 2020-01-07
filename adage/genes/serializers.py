from rest_framework import serializers
from organisms.serializers import OrganismSerializer
from .models import Gene
from django.db.models.fields import FloatField

class GeneSerializer(serializers.ModelSerializer):
    # Extra field to indicate which field has the best match in trigram search
    max_similarity_field = serializers.CharField(default=None)

    # Full information of organism (instead of a plain ID):
    organism = OrganismSerializer()

    class Meta:
        model = Gene
        fields = '__all__'
