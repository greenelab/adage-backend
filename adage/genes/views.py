import json
from django.db.models import Case, CharField, F, Q, Value, When
from django.db.models.functions import Cast, Greatest
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector, TrigramSimilarity
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from genes.models import Gene
from genes.serializers import GeneSerializer


class GeneViewSet(ModelViewSet):
    """
    Gene viewset.
    Supported parameters: `organism`, `search`, `autocomplete`.
    """

    http_method_names = ['get', 'post']
    serializer_class = GeneSerializer
    filterset_fields = ['organism', ]

    def create(self, request):
        """This method takes care of `POST` requests."""

        queryset = Gene.objects.all()
        json_req = json.loads(request.body)

        # Handle "pk__in" parameter in `POST` request
        gene_ids = json_req.get('pk__in', None)
        if gene_ids:
            gene_ids = [int(x) for x in gene_ids.split(',')]
            queryset = queryset.filter(pk__in=gene_ids)

        # Wrap the data to the same structure as the one in `GET` request
        resp_data = {
            'results': GeneSerializer(queryset, many=True).data
        }
        return Response(resp_data)

    @staticmethod
    def full_text_search(search_str, queryset):
        """The full text search is performed on the following 4 fields:
         - "standard_name": highest priority (A: 1.0);
         - "systematic_name": second highest priority (B: 0.4);
         - "description" and "crossref__xrid": lowest priority (C: 0.2).
        """

        standard_vector = SearchVector(
            'standard_name', weight='A', config='english'
        )
        systematic_vector = SearchVector(
            'systematic_name', weight='B', config='english'
        )
        other_vector = SearchVector(
            'aliases', weight='C', config='english'
        )

        vectors = standard_vector + systematic_vector + other_vector
        query = SearchQuery(search_str, config='english')
        queryset = queryset.annotate(
            rank=SearchRank(vectors, query)
        ).filter(rank__gte=0.1
        ).order_by('-rank', 'standard_name')

        return queryset

    def get_queryset(self):
        queryset = Gene.objects.all()
        # Extract the 'search' parameter from the incoming query and perform
        # full text search.
        search_str = self.request.query_params.get('search', None)
        if search_str is not None:
            queryset = self.full_text_search(search_str, queryset)

        # Extract the 'autocomplete' parameter from the incoming query and
        # perform trigram search on the following 3 fields in Gene model:
        # - "standard_name" (multiplied by 2.0 to give it a higher priority)
        # - "systematic_name"
        # - "description"
        # - entrezid" (converted to string)
        similarity_str = self.request.query_params.get('autocomplete', None)
        if similarity_str is not None:
            queryset = queryset.annotate(
                eid_str=Case(
                    When(entrezid__isnull=False,
                         then=Cast('entrezid', output_field=CharField())
                    ),
                    default=Value(''),
                    output_field=CharField(),
                )
            ).annotate(
                std_similarity=TrigramSimilarity('standard_name', similarity_str),
                sys_similarity=TrigramSimilarity('systematic_name', similarity_str),
                alias_similarity=TrigramSimilarity('aliases', similarity_str),
                desc_similarity=TrigramSimilarity('description', similarity_str),
                eid_similarity=TrigramSimilarity('eid_str', similarity_str),
            ).annotate(
                similarity=(
                    F('std_similarity') + F('sys_similarity') + F('alias_similarity') +
                    F('desc_similarity') + F('eid_similarity')
                ),
                max_similarity=Greatest(
                    'std_similarity', 'sys_similarity', 'alias_similarity',
                    'desc_similarity', 'eid_similarity'
                )
            ).annotate(
                max_similarity_field=Case(
                    When(std_similarity__gte=F('max_similarity'),
                         then=Value("standard_name")
                    ),
                    When(sys_similarity__gte=F('max_similarity'),
                         then=Value("systematic_name")
                    ),
                    When(alias_similarity__gte=F('max_similarity'),
                         then=Value("aliases")
                    ),
                    When(desc_similarity__gte=F('max_similarity'),
                         then=Value("description")
                    ),
                    When(eid_similarity__gte=F('max_similarity'),
                         then=Value("entrezid")
                    ),
                    output_field=CharField(),
                )
            ).filter(similarity__gte=0.1
            ).order_by('-max_similarity', '-similarity', 'standard_name')

        return queryset
