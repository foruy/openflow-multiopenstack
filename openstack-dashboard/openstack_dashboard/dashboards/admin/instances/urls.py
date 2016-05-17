from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.instances import views

urlpatterns = patterns('openstack_dashboard.dashboards.admin.instances.views',
    url(r'^$', views.AdminIndexView.as_view(), name='index'),
)
