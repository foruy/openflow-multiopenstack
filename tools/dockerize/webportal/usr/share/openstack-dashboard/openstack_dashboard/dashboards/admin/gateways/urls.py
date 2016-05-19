from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.gateways import views

urlpatterns = patterns('openstack_dashboard.dashboards.admin.gateways.views',
    url(r'^$', views.AdminIndexView.as_view(), name='index'),
    url(r'^(?P<id>[^/]+)$', views.SettingView.as_view(), name='setting'),
)
