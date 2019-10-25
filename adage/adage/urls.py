"""adage URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from analyze.views import ExperimentViewSet, MLModelViewSet
from genes.views import GeneViewSet

router = routers.DefaultRouter()
router.register(r"experiments", ExperimentViewSet, basename="experiment")
router.register(r"mlmodels", MLModelViewSet)
router.register(r"genes", GeneViewSet,  basename="genes")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
]
