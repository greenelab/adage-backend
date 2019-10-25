from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Gene
from .serializers import GeneSerializer


class GeneViewSet(ReadOnlyModelViewSet):
    """Genes viewset"""

    http_method_names = ['get']
    serializer_class = GeneSerializer

    def get_queryset(self):
        queryset = Gene.objects.all()

        # 'search' parameter, which does full text search based on the
        # following four fields in Gene model:
        # - "standard_name": highest priority (A: 1.0);
        # - "systematic_name": second highest priority (B: 0.4);
        # - "description" and "crossref__xrid": lowest priority (C: 0.2).
        search_str = self.request.query_params.get('search', None)
        if search_str is not None:
            from django.contrib.postgres.search import (
                SearchQuery, SearchRank, SearchVector
            )

            standard_vector = SearchVector('standard_name', weight='A')
            systematic_vector = SearchVector('systematic_name', weight='B')
            other_vector = SearchVector(
                'description', 'crossref__xrid', weight='C'
            )

            vectors = standard_vector + systematic_vector + other_vector
            query = SearchQuery(search_str)
            queryset = queryset.annotate(
                rank=SearchRank(vectors, query)
            ).filter(rank__gte=0.1
            ).order_by('-rank', 'standard_name')

        # 'autocomplete' parameter, which does trigram search based on the
        # following three fields in Gene model:
        # - "standard_name" (multiplied by 2.0 to give it a higher priority)
        # - "systematic_name"
        # - "description"
        similarity_str = self.request.query_params.get('autocomplete', None)
        if similarity_str is not None:
            from django.contrib.postgres.search import TrigramSimilarity

            queryset = queryset.annotate(
                similarity=(
                    TrigramSimilarity('standard_name', similarity_str) * 2.0 +
                    TrigramSimilarity('systematic_name', similarity_str) +
                    TrigramSimilarity('description', similarity_str)
                )
            ).filter(similarity__gte=0.1
            ).order_by('-similarity', 'standard_name')

        return queryset
