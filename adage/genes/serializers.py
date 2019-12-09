from rest_framework import serializers
from .models import Gene
from django.db.models.fields import FloatField

class GeneSerializer(serializers.ModelSerializer):
    # Extra fields for similarity search
    std_similarity = serializers.FloatField()
    sys_similarity = serializers.FloatField()
    desc_similarity = serializers.FloatField()

    class Meta:
        model = Gene
        fields = '__all__'
