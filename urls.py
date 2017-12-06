from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^single/$', views.single, name='single'),
    url(r'^beta/single/$', views.single, name='beta-single'),
    url(r'^batch/$', views.batch, name='batch'),
    url(r'^within/$', views.within, name='within'),
    url(r'^data_within/$', views.data_within, name='data_within'),
    url(r'^progress/$', views.get_progress, name='get_progress'),
    url(r'^get_collected_data/$', views.get_collected_data, name='get_collected_data'),
    
    # Beta
    url(r'^v1/parcels/(?P<parcel_ids>[\w,]*)$', views.beta_parcels, name='single_parcel'),
    url(r'^beta/parcels/(?P<parcel_ids>[\w,]*)$', views.beta_parcels, name='single_parcel'),
]