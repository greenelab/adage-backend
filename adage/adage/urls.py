"""adage URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from analyze.views import (
    ActivityViewSet,
    EdgeViewSet,
    ExperimentViewSet,
    MLModelViewSet,
    SampleViewSet,
    SignatureViewSet,
    ParticipationTypeViewSet,
    ParticipationViewSet,
)
from genes.views import GeneViewSet
from organisms.views import OrganismViewSet

router = routers.DefaultRouter()

router.register(r"activity", ActivityViewSet, basename='activity')
router.register(r"edge", EdgeViewSet, basename='edge')
router.register(r"experiment", ExperimentViewSet, basename="experiment")
router.register(r"gene", GeneViewSet, basename="gene")
router.register(r"model", MLModelViewSet)
router.register(r"organism", OrganismViewSet)
router.register(r"sample", SampleViewSet)
router.register(r"signature", SignatureViewSet)
router.register(r"participationtype", ParticipationTypeViewSet)
router.register(
    r"participation",
    ParticipationViewSet,
    basename='participation'
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('tribe_client/', include('tribe_client.urls')),
]
