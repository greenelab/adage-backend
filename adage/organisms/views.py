from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Organism
from .serializers import OrganismSerializer


class OrganismViewSet(ReadOnlyModelViewSet):
    """Organisms viewset."""

    serializer_class = OrganismSerializer
    queryset = Organism.objects.all()
