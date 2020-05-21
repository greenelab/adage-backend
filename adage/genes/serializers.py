from rest_framework import serializers
from .models import Gene


class GeneSerializer(serializers.ModelSerializer):
    # Optional external URL for each gene, based on "url_template" field
    # in Organism model
    external_url = serializers.URLField(
        required=False,
        read_only=True,
        source="get_external_url"
    )

    # This field is only populated when `autocomplete` parameter is in the URL
    max_similarity_field = serializers.CharField(
        required=False,
        read_only=True
    )

    # FIXME: "entrezid" is an alias of "entrez_id". It is created to prevent
    # front-end from breaking.
    # It should be deleted once the front-end uses "entrez_id".
    entrezid = serializers.IntegerField(read_only=True, source="entrez_id")

    class Meta:
        model = Gene
        fields = '__all__'
