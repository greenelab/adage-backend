from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import MLModel
from .serializers import MLModelSerializer


@api_view(['GET'])
def api_root(request):
    """Main API"""
    return Response({
        'mlmodels': reverse('mlmodel-list', request=request),
    })


class MLModelViewSet(ReadOnlyModelViewSet):
    """Machine learning model viewset"""

    http_method_names = ['get']
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
