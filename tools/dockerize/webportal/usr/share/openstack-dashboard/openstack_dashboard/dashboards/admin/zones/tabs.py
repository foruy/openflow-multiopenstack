from django.utils.translation import ugettext_lazy as _

from horizon import tabs
from horizon import exceptions

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.zones.images \
    import tables as image_tables
from openstack_dashboard.dashboards.admin.zones.flavors \
    import tables as flavor_tables
from openstack_dashboard.dashboards.admin.zones.gateways \
    import tables as gateway_tables
from openstack_dashboard.dashboards.admin.zones.networks \
    import tables as network_tables

class ImageTab(tabs.TableTab):
    table_classes = (image_tables.ImagesTable,)
    name = _("Image")
    slug = "image_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_images_data(self):
        try:
            images = api.proxy.image_get(
                    self.request, self.tab_group.kwargs['zone'])
        except Exception:
            images = []
            exceptions.handle(self.request,
                              _('Unable to retrieve images.'),
                              ignore=True)
        return images

class FlavorTab(tabs.TableTab):
    table_classes = (flavor_tables.FlavorsTable,)
    name = _("Flavor")
    slug = "flavor_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_flavors_data(self):
        try:
            flavors = api.proxy.flavor_get_by_zone(
                    self.request, self.tab_group.kwargs['zone'])
        except Exception:
            flavors = []
            exceptions.handle(self.request, _("Unable to retrieve flavors."))
        return flavors 

class GatewayTab(tabs.TableTab):
    table_classes = (gateway_tables.GatewaysTable,)
    name = _("Gateway")
    slug = "gateway_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_gateways_data(self):
        try:
            gateways = api.proxy.gateway_get_by_zone(
                    self.request, self.tab_group.kwargs['zone'])
        except Exception:
            gateways = []
            exceptions.handle(self.request, _("Unable to retrieve gateways."))
        return gateways

class NetworkTab(tabs.TableTab):
    table_classes = (network_tables.NetworksTable,)
    name = _("Network")
    slug = "network_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_networks_data(self):
        msg = _("Unable to retrieve networks.")
        try:
            networks = api.proxy.network_get_by_zone(
                    self.request, self.tab_group.kwargs['zone'])
        except Exception:
            networks = []
            exceptions.handle(self.request, msg)

        try:
            network_types = api.proxy.network_type_list(self.request)
        except:
            network_types = []
            exceptions.handle(self.request, msg, ignore=True)

        netype_dict = dict((nt.id, nt.cidr) for nt in network_types)

        for net in networks:
            net.cidr = netype_dict.get(net.netype, net.netype)

        return networks

class DetailTabs(tabs.TabGroup):
    slug = "image_and_flavor_and_gateway"
    tabs = (ImageTab, FlavorTab, GatewayTab, NetworkTab)
    sticky = True
