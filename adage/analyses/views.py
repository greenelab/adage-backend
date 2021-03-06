from django.db.models import Case, CharField, F, IntegerField, Q, Value, When
from django.db.models.functions import Greatest
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector, TrigramSimilarity
)
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.exceptions import ParseError

from .models import (
    Experiment, MLModel, Sample, Signature, Activity, Edge,
    ParticipationType, Participation,
)

from .serializers import (
    ActivitySerializer,
    ExperimentSerializer,
    MLModelSerializer,
    SampleSerializer,
    SignatureSerializer,
    EdgeSerializer,
    ParticipationTypeSerializer,
    ParticipationSerializer,
)

class ExperimentViewSet(ReadOnlyModelViewSet):
    """
    Experiment viewset.
    Supported parameters: `accession`, `autocomplete`, `search`.
    """

    serializer_class = ExperimentSerializer
    filterset_fields = ['accession', ]

    def get_queryset(self):
        queryset = Experiment.objects.all().order_by('accession')

        # Extract the 'search' parameter from the incoming query and perform
        # a full text search on the following fields in Experiment model:
        # - "accession"
        # - "name"
        # - "description"
        # - "samples_info"
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

        # Extract the 'autocomplete' parameter from the incoming query and
        # perform trigram search on "accession" field and substring search on
        # the following fields:
        # - "name"
        # - "description"
        # The reason why trigram search is not used on these fields is because
        # when values of these fields are long strings, trigram similarity
        # score becomes tiny.
        similarity_str = self.request.query_params.get('autocomplete', None)
        if similarity_str is not None:
            queryset = queryset.annotate(
                accession_match=TrigramSimilarity(
                    'accession', similarity_str
                )
            ).filter(
                Q(accession_match__gt=0.1) |
                Q(name__icontains=similarity_str) |
                Q(description__icontains=similarity_str)
            ).annotate(
                name_match=Case(
                    When(name__icontains=similarity_str, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                desc_match=Case(
                    When(description__icontains=similarity_str, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            ).annotate(
                max_similarity_field=Case(
                    When(accession_match__gte=0.1, then=Value("accession")),
                    When(name_match=1, then=Value("name")),
                    When(desc_match=1, then=Value("description")),
                    output_field=CharField()
                )
            ).order_by(
                '-accession_match', '-name_match', '-desc_match'
            )

        return queryset


class MLModelViewSet(ReadOnlyModelViewSet):
    """Machine learning model viewset."""

    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer


class SampleViewSet(ReadOnlyModelViewSet):
    """Sample viewset."""

    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


class SignatureViewSet(ReadOnlyModelViewSet):
    """
    Signature viewset.
    Supported parameter: `mlmodel`
    """

    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    filterset_fields = ['mlmodel', ]


class ActivityViewSet(ReadOnlyModelViewSet):
    """
    Activity viewset.
    Supported parameters: `mlmodel`, `samples`, `signatures`
    """

    serializer_class = ActivitySerializer

    def get_queryset(self):
        queryset = Activity.objects.all()

        # If "mlmodel" parameter is found in URL, always handle it first.
        mlmodel = self.request.query_params.get('mlmodel', None)
        if mlmodel:
            try:
                mlmodel_id = int(mlmodel)
            except ValueError:
                raise ParseError(
                    {'error': f'mlmodel not an integer: {mlmodel}'}
                )
            queryset = queryset.filter(
                signature__mlmodel=mlmodel_id
            ).order_by('sample', 'signature')

        # Handle "samples" parameter in URL
        samples = self.request.query_params.get('samples', None)
        if samples:
            try:
                sample_ids = {int(id) for id in samples.split(',')}
            except ValueError:
                raise ParseError(
                    {'error': f'sample IDs not integers: {samples}'}
                )
            queryset = queryset.filter(sample__in=sample_ids).order_by('sample')

        # Handle "signatures" parameter in URL
        signatures = self.request.query_params.get('signatures', None)
        if signatures:
            try:
                signature_ids = {int(id) for id in signatures.split(',')}
            except ValueError:
                raise ParseError(
                    {'error': f'signature IDs not integers: {signatures}'}
                )
            queryset = queryset.filter(signature__in=signature_ids).order_by('signature')

        return queryset


class EdgeViewSet(ReadOnlyModelViewSet):
    """
    Gene-gene edge viewset.
    Supported parameter: `mlmodel`, `genes`.
    """

    serializer_class = EdgeSerializer

    def get_queryset(self):
        queryset = Edge.objects.all()

        # If "mlmodel" parameter is found, always handle it first.
        mlmodel = self.request.query_params.get('mlmodel', None)
        if mlmodel:
            try:
                mlmodel_id = int(mlmodel)
            except ValueError:
                raise ParseError(
                    {'error': f'mlmodel not an integer: {mlmodel}'}
                )
            queryset = queryset.filter(mlmodel=mlmodel_id)

        # Handle "genes" parameter
        genes = self.request.query_params.get('genes', None)
        if genes:
            try:
                gene_ids = {int(id) for id in genes.split(',')}
            except ValueError:
                raise ParseError(
                    {'error': f'gene IDs not integers: {genes}'}
                )
            qset = Q(gene1__in=gene_ids) | Q(gene2__in=gene_ids)
            direct_edges = queryset.filter(qset).distinct()
            related_genes = set()
            for e in direct_edges:
                related_genes.add(e.gene1)
                related_genes.add(e.gene2)
            queryset = queryset.filter(
                gene1__in=related_genes, gene2__in=related_genes
            ).distinct()

        return queryset.order_by('-weight')


class ParticipationTypeViewSet(ReadOnlyModelViewSet):
    """
    ParticipationType viewset.
    Supported parameter: `name`.
    """

    queryset = ParticipationType.objects.all()
    serializer_class = ParticipationTypeSerializer
    filterset_fields = ['name', ]

class ParticipationViewSet(ReadOnlyModelViewSet):
    """
    Signature-gene participation viewset.
    Supported parameters: `signature`, `gene`, `participation_type`,
    `related-genes`.
    """

    serializer_class = ParticipationSerializer
    filterset_fields = ['signature', 'gene', 'participation_type', ]

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
