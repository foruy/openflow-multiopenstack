from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

class RebuildNetwork(tables.LinkAction):
    name = "rebuild"
    verbose_name = _("Rebuild Network")
    url = "horizon:admin:zones:network_rebuild"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum=None):
        return reverse(self.url, args=(self.table.kwargs["zone"],))

class DeleteNetwork(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Network")
    data_type_plural = _("Networks")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("network", "network:delete"),)

    def action(self, request, obj_id):
        api.proxy.network_delete(request, obj_id)

class NetworksTable(tables.DataTable):
    gateway = tables.Column("gateway",
                            verbose_name=_("Gateway"))
    cidr = tables.Column("cidr",
                           verbose_name=_("Network CIDR"))
    class Meta:
        name = "networks"
        verbose_name = _("Networks")
        table_actions = (RebuildNetwork, DeleteNetwork,)
        row_actions = (DeleteNetwork,)
