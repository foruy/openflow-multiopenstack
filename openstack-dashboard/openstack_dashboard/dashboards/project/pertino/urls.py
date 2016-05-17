
from django.conf.urls import include  # noqa
from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.pertino import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^display_list/(?P<display_type>[^/]+)/$', views.device_display, name='device_display'),
 #   url(r'^device_detail/(?P<device_id>[^/]+)/$', views.device_detail, name='device_detail'),
    url(r'^add/$', views.AddView.as_view(), name='add'),
)
