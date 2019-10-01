"""adage URL Configuration"""

from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from analyze import views

router = routers.DefaultRouter()
router.register(r"mlmodels", views.MLModelViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', views.api_root),
    path('api/v1/', include(router.urls)),
]
