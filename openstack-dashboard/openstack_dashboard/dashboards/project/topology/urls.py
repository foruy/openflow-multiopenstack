from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.topology import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^json$', views.JSONView.as_view(), name='json')
)
