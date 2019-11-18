from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Organism
from .serializers import OrganismSerializer


class OrganismViewSet(ReadOnlyModelViewSet):
    """Organisms viewset."""

    http_method_names = ['get']
    serializer_class = OrganismSerializer
    queryset = Organism.objects.all()
