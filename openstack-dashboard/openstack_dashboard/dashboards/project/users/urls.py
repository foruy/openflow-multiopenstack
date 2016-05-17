from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.users import views

urlpatterns = patterns('openstack_dashboard.dashboards.project.users.views',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<source_name>[^/]+)/(?P<source_id>[^/]+)$',
        views.DetailView.as_view(), name='detail'),
)
