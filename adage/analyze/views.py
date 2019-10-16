from rest_framework import filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Experiment, MLModel
from .serializers import ExperimentSerializer, MLModelSerializer


class ExperimentViewSet(ReadOnlyModelViewSet):
    http_method_names = ['get']
    serializer_class = ExperimentSerializer
    filter_backends = (filters.SearchFilter, )

    def get_queryset(self):
        queryset = Experiment.objects.all()
        # 'search' parameter
        search_str = self.request.query_params.get('search', None)
        if search_str is not None:
            from django.contrib.postgres.search import (
                SearchQuery, SearchRank, SearchVector
            )
            # In AWS Postgres RDS, the default config is 'simple'.
            # We use 'english' to make the text search more flexible.
            vector = SearchVector('accession', 'name', 'description',
                                  config='english'
            )
            query = SearchQuery(search_str, config='english')
            queryset = queryset.annotate(
                rank=SearchRank(vector, query)
            ).filter(rank__gte=0.01
            ).order_by('-rank', 'accession')

        for x in queryset:
            print(x.rank)

        return queryset


class MLModelViewSet(ReadOnlyModelViewSet):
    """Machine learning model viewset"""

    http_method_names = ['get']
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
