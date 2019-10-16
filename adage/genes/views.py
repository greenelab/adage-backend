# Create your views here.
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Gene
from .serializers import GeneSerializer


class GeneViewSet(ReadOnlyModelViewSet):
    http_method_names = ['get']
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
