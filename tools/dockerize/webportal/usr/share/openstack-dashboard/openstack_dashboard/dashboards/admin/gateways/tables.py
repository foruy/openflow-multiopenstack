from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters

from openstack_dashboard import api

class RemoveGateway(tables.BatchAction):
    name = "remove"
    action_present = _("Remove")
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Gateway")
    data_type_plural = _("Gateways")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("gateway", "gateway:delete"),)

    def allowed(self, request, gateway=None):
        if gateway is not None:
            return gateway.int_dev != gateway.ext_dev
        return False

    def action(self, request, obj_id):
        api.proxy.gateway_delete(request, obj_id)

class SettingGateway(tables.LinkAction):
    name = "setting"
    verbose_name = _("Setting Gateway")
    url = "horizon:admin:gateways:setting"
    classes = ("btn-launch", "ajax-modal")

class GatewaysTable(tables.DataTable):
    hostname = tables.Column("hostname",
                         verbose_name=_("Host Name"))
    int_ip = tables.Column("int_ip",
                         verbose_name=_("Internal Address"))
    int_mac = tables.Column("int_mac",
                         verbose_name=_("Internal MAC Address"))
    ext_ip = tables.Column("ext_ip",
                         verbose_name=_("Public Address"))
    int_mac = tables.Column("ext_mac",
                         verbose_name=_("Public MAC Address"))
    idc_id = tables.Column("idc_id",
                         verbose_name=_("IDC ID"))
    class Meta:
        name = "gateways"
        verbose_name = _("Gateways")
        #table_actions = (RemoveGateway,)
        row_actions = (SettingGateway,)
        #row_actions = (RemoveGateway, SettingGateway)
