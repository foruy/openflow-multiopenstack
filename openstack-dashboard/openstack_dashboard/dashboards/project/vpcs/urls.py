
from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.vpcs import views

VIEW_MOD = 'openstack_dashboard.dashboards.project.vpcs.views'

urlpatterns = patterns(VIEW_MOD,
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^show/$', 'show', name='show'),
    url(r'^create/$', 'create', name='create'),
    url(r'^delete/$', 'delete', name='delete'),
    #url(r'^launch/$', 'launch', name='launch'),
    url(r'^launch/(?P<zone_id>[^/]+)$', 'launch', name='launch'),
    url(r'^get_servers/$', 'get_servers', name='get_servers'),
    url(r'^get_dcs/$', 'get_dcs', name='get_dcs'),
    url(r'^stop/(?P<instance_id>[^/]+)/$', 'stop',  name="stop"),
    url(r'^start/(?P<instance_id>[^/]+)/$', 'start',  name="start"),
    url(r'^terminate/(?P<instance_id>[^/]+)/$', 'terminate', name="terminate"),
)
