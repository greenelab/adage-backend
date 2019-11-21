"""adage URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from analyze.views import (
    EdgeViewSet,
    ExperimentViewSet,
    MLModelViewSet,
    SampleViewSet,
    SignatureViewSet,
)
from genes.views import GeneViewSet
from organisms.views import OrganismViewSet

router = routers.DefaultRouter()
router.register(r"edge", EdgeViewSet)
router.register(r"experiment", ExperimentViewSet, basename="experiment")
router.register(r"gene", GeneViewSet, basename="gene")
router.register(r"model", MLModelViewSet)
router.register(r"organism", OrganismViewSet)
router.register(r"sample", SampleViewSet)
router.register(r"signature", SignatureViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
]
