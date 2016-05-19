from django.conf.urls import patterns, url

from views import IndexView
VIEW_MOD = 'openstack_dashboard.dashboards.project.bill.views'


urlpatterns = patterns(VIEW_MOD,
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^all/$', "get_all", name="all"),
)
