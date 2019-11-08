from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Experiment, MLModel
from .serializers import ExperimentSerializer, MLModelSerializer


class ExperimentViewSet(ReadOnlyModelViewSet):
    """Experiments viewset."""

    http_method_names = ['get']
    serializer_class = ExperimentSerializer

    def get_queryset(self):
        queryset = Experiment.objects.all()

        # Extract the 'search' parameter from the incoming query and perform
        # a full text search on the following 3 fields in Experiment model:
        # - "accession"
        # - "name"
        # - "description"
        search_str = self.request.query_params.get('search', None)
        if search_str is not None:
            # Use 'english' config to enable word stemming (default is "simple")
            vector = SearchVector(
                'accession', 'name', 'description', config='english'
            )
            query = SearchQuery(search_str, config='english')
            queryset = queryset.annotate(
                rank=SearchRank(vector, query)
            ).filter(rank__gte=0.05
            ).order_by('-rank', 'accession')

        return queryset


class MLModelViewSet(ReadOnlyModelViewSet):
    """Machine learning models viewset."""

    http_method_names = ['get']
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
