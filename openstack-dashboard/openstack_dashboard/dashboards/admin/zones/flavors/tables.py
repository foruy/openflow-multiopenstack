from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

class RebuildFlavor(tables.LinkAction):
    name = "rebuild"
    verbose_name = _("Rebuild Flavor")
    url = "horizon:admin:zones:flavor_rebuild"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum=None):
        return reverse(self.url, args=(self.table.kwargs["zone"],))

class DeleteFlavor(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Flavor")
    data_type_plural = _("Flavors")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("flavor", "flavor:delete"),)

    def action(self, request, obj_id):
        api.proxy.flavor_delete(request, obj_id)

class FlavorsTable(tables.DataTable):
    flavorid = tables.Column("flavorid",
                         verbose_name=_("Flavor Id"))
    name = tables.Column("name",
                         verbose_name=_("Flavor Name"))
    #zone = tables.Column("zone",
    #                     verbose_name=_("Availability Zone"))
    vcpus = tables.Column("vcpus",
                         verbose_name=_("VCPUs"))
    ram = tables.Column("ram",
                         verbose_name=_("RAM"))
    disk = tables.Column("disk",
                         verbose_name=_("Disk"))
    swap = tables.Column("swap",
                         verbose_name=_("Swap"))
    ephemeral = tables.Column("ephemeral",
                         verbose_name=_("Ephemeral"))
    is_public = tables.Column("is_public",
                         verbose_name=_("Public"))
    class Meta:
        name = "flavors"
        verbose_name = _("Flavors")
        table_actions = (RebuildFlavor, DeleteFlavor,)
        row_actions = (DeleteFlavor,)
