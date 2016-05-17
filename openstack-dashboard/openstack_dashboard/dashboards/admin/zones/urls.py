from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.zones import views
from openstack_dashboard.dashboards.admin.zones.images \
    import views as image_views
from openstack_dashboard.dashboards.admin.zones.flavors \
    import views as flavor_views
from openstack_dashboard.dashboards.admin.zones.gateways \
    import views as gateway_views
from openstack_dashboard.dashboards.admin.zones.networks \
    import views as network_views

REBUILD = r'^rebuild/(?P<zone>[^/]+)/%s$'

urlpatterns = patterns('openstack_dashboard.dashboards.admin.zones.views',
    url(r'^$', views.AdminIndexView.as_view(), name='index'),
    url(r'^create/$', views.AdminCreateView.as_view(), name='create'),
    url(r'^(?P<zone>[^/]+)$', views.AdminDetailView.as_view(), name='detail'),
    url(REBUILD % 'image', image_views.RebuildView.as_view(), name='image_rebuild'),
    url(REBUILD % 'flavor', flavor_views.RebuildView.as_view(), name='flavor_rebuild'),
    url(REBUILD % 'gateway', gateway_views.RebuildView.as_view(), name='gateway_rebuild'),
    url(REBUILD % 'network', network_views.RebuildView.as_view(), name='network_rebuild'),
)
