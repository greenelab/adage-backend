from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.exceptions import ParseError
from .models import (
    Experiment, MLModel, Sample, Signature, Edge, ParticipationType,
    Participation,
)
from .serializers import (
    ExperimentSerializer,
    MLModelSerializer,
    SampleSerializer,
    SignatureSerializer,
    EdgeSerializer,
    ParticipationTypeSerializer,
    ParticipationSerializer,
)

class ExperimentViewSet(ReadOnlyModelViewSet):
    """Experiment viewset. Supported parameters: `accession`, `search`"""

    http_method_names = ['get']
    serializer_class = ExperimentSerializer
    filterset_fields = ['accession', ]

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
                'accession', 'name', 'description', 'samples_info',
                config='english'
            )
            query = SearchQuery(search_str, config='english')
            queryset = queryset.annotate(
                rank=SearchRank(vector, query)
            ).filter(rank__gte=0.05
            ).order_by('-rank', 'accession')
        else:
            queryset = queryset.order_by('accession')

        return queryset


class MLModelViewSet(ReadOnlyModelViewSet):
    """Machine learning model viewset."""

    http_method_names = ['get']
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer


class SampleViewSet(ReadOnlyModelViewSet):
    """Sample viewset."""

    http_method_names = ['get']
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


class SignatureViewSet(ReadOnlyModelViewSet):
    """Signature viewset. Supported parameter: `mlmodel`"""

    http_method_names = ['get']
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    filterset_fields = ['mlmodel', ]


class EdgeViewSet(ReadOnlyModelViewSet):
    """Gene-gene edge viewset. Supported parameter: `mlmodel`"""

    http_method_names = ['get']
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer
    filterset_fields = ['mlmodel', ]


class ParticipationTypeViewSet(ReadOnlyModelViewSet):
    """ParticipationType viewset."""

    http_method_names = ['get']
    queryset = ParticipationType.objects.all()
    serializer_class = ParticipationTypeSerializer


class ParticipationViewSet(ReadOnlyModelViewSet):
    """
    Signature-gene participation viewset.
    Supported parameter: `related-genes`.
    """

    http_method_names = ['get']
    serializer_class = ParticipationSerializer

    def get_queryset(self):
        queryset = Participation.objects.all()

        related_genes = self.request.query_params.get('related-genes', None)
        if related_genes:
            try:
                query_genes = {int(id) for id in related_genes.split(',')}
            except ValueError:
                raise ParseError(
                    {'error': f'Invalid gene IDs: {related_genes}'}
                )

            signatures = queryset.filter(
                gene__in=query_genes
            ).values('signature').distinct()

            queryset = queryset.filter(signature__in=signatures)

        return queryset
