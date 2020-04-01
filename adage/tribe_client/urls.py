from django.conf.urls import url
from tribe_client import views

urlpatterns = [
    url(r'^$', views.connect_to_tribe, name='connect_to_tribe'),
    url(r'^get_settings$', views.get_settings, name='get_settings'),
    url(r'^logout$', views.logout_from_tribe, name='logout_from_tribe'),
    url(r'^get_token$', views.get_token, name='get_token'),

    url(
        r'^display_genesets/$',
        views.display_genesets,
        name='display_genesets'
    ),

    url(
        r'^display_geneset_versions/(?P<geneset>[-_\w]+)/$',
        views.display_versions,
        name='display_versions'
    ),

    url(r'^token$', views.return_access_token, name='return_access_token'),
    url(r'^return_user$', views.return_user_obj, name='return_user'),
    url(r'^create_geneset$', views.create_geneset, name='create_geneset'),

    url(
        r'^return_unpickled_genesets$',
        views.return_unpickled_genesets,
        name='return_unpickled_genesets'
    )
]
