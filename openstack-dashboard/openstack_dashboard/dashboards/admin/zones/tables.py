import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

class CreateLink(tables.LinkAction):
    name = "create_zone"
    verbose_name = _("Create Zone")
    url = "horizon:admin:zones:create"
    classes = ("btn-launch", "ajax-modal")

class DeleteZone(tables.BatchAction):
    name = "delete_zone"
    action_present = _("Terminate")
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Zone")
    data_type_plural = _("Zones")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("image", "image:delete"),)

    def action(self, request, obj_id):
        api.proxy.zone_delete(request, obj_id)

class DetailLink(tables.LinkAction):
    name = "detail"
    verbose_name = _("Edit")
    url = "horizon:admin:zones:detail"

class AdminZonesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Zone Name"))
    auth_url = tables.Column("auth_url",
                         verbose_name=_("Auth URL"))
    class Meta:
        name = "zones"
        verbose_name = _("Zones")
        table_actions = (CreateLink,)
        row_actions = (DetailLink, DeleteZone)
