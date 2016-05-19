from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.users import views

urlpatterns = patterns('openstack_dashboard.dashboards.admin.users.views',
    url(r'^$', views.AdminIndexView.as_view(), name='index'),
    url(r'^(?P<user_id>[^/]+)$', views.AdminRecordView.as_view(), name='record'),
    url(r'^(?P<user_id>[^/]+)/(?P<source_name>[^/]+)/(?P<source_id>[^/]+)$',
        views.AdminDetailView.as_view(), name='detail'),
)
