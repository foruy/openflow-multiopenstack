import logging
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api
LOG = logging.getLogger(__name__)

class RebuildImage(tables.LinkAction):
    name = "rebuild"
    verbose_name = _("Rebuild Image")
    url = "horizon:admin:zones:image_rebuild"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum=None):
        return reverse(self.url, args=(self.table.kwargs["zone"],))

class DeleteImage(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Scheduled termination of %(data_type)s")
    data_type_singular = _("Image")
    data_type_plural = _("Images")
    classes = ('btn-danger', 'btn-terminate')
    policy_rules = (("image", "image:delete"),)

    def action(self, request, obj_id):
        api.proxy.image_delete(request, obj_id)

class ImagesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Image Name"))
    #zone = tables.Column("zone",
    #                     verbose_name=_("Availability Zone"))
    container_format = tables.Column("container_format",
                         verbose_name=_("Container Format"))
    disk_format = tables.Column("disk_format",
                         verbose_name=_("Disk Format"))
    property = tables.Column("property",
                         verbose_name=_("Property"))
    size = tables.Column("size",
                         verbose_name=_("Size"))
    
    class Meta:
        name = "images"
        verbose_name = _("Images")
        table_actions = (RebuildImage, DeleteImage,)
        row_actions = (DeleteImage,)
