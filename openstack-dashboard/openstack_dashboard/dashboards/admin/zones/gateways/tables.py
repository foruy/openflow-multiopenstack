from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

class RebuildGateway(tables.LinkAction):
    name = "rebuild"
    verbose_name = _("Rebuild Gateway")
    url = "horizon:admin:zones:gateway_rebuild"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum=None):
        return reverse(self.url, args=(self.table.kwargs["zone"],))

class DeleteGateway(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Gateway")
    data_type_plural = _("Gateways")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("gateway", "gateway:delete"),)

    def action(self, request, obj_id):
        api.proxy.gateway_delete(request, obj_id)

class GatewaysTable(tables.DataTable):
    hostname = tables.Column("hostname",
                         verbose_name=_("Host Name"))
    datapath = tables.Column("datapath_id",
                         verbose_name=_("DataPath ID"))
    int_ip = tables.Column("int_ip",
                         verbose_name=_("Internal Address"))
    int_mac = tables.Column("int_mac",
                         verbose_name=_("Internal MAC Address"))
    ext_ip = tables.Column("ext_ip",
                         verbose_name=_("Public Address"))
    int_mac = tables.Column("ext_mac",
                         verbose_name=_("Public MAC Address"))
    count = tables.Column("count",
                         verbose_name=_("Count"))
    idc_id = tables.Column("idc_id",
                         verbose_name=_("IDC ID"))
    class Meta:
        name = "gateways"
        verbose_name = _("Gateways")
        table_actions = (RebuildGateway, DeleteGateway)
        row_actions = (DeleteGateway,)
