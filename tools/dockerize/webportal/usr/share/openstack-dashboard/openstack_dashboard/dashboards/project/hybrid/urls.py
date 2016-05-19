from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.hybrid import views

VIEW_MOD = 'openstack_dashboard.dashboards.project.hybrid.views'

urlpatterns = patterns(VIEW_MOD,
        url(r'^$', views.IndexView.as_view(), name='index'),
)

