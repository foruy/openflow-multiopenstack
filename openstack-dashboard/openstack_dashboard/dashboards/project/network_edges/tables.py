import logging
from django import template
from django.conf import settings
from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

class Firewall(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Firewall Rules")
    url = "horizon:project:network_edges:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, instance=None):
        #if instance.addresses.items():
        if instance and instance.addresses and instance.status != 'UNKNOWN':
            return True
        return False

    def get_link_url(self, instance):
        base_url = urlresolvers.reverse(self.url, args=(instance.id,))
        return base_url

class DeleteFirewall(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleting")
    data_type_singular = _("Firewall Rule")
    data_type_plural = _("Firewall Rules")
    classes = ('btn-danger', 'btn-detach')

    def action(self, request, obj_id):
        api.proxy.firewall_delete(request, obj_id)

    def get_success_url(self, request):
        return reverse('horizon:project:network_edges:index')

#class CreateFirewall(tables.LinkAction):
#    name = "add_firewall"
#    verbose_name = _("Add Firewall Rule")
#    url = "horizon:project:network_edges:add_firewall"
#    classes = ("ajax-modal", "btn-create")

def get_firewall(instance):
    template_name = 'project/network_edges/_firewall_list.html'
    context = {"firewall": instance.firewall}
    return template.loader.render_to_string(template_name, context)

def get_ips(instance):
    ips = [addr['address'] for addr in instance.addresses]
    return '|'.join(ips)


class InstancesTable(tables.DataTable):
    name = tables.Column("name",
                         #link=("horizon:project:instances:detail"),
                         verbose_name=_("Instance Name"))

    address = tables.Column(get_ips,
                            verbose_name=_("IP Address"),
                            attrs={'data-type': "ip"})
    firewall = tables.Column(get_firewall, verbose_name=_("Ingress Rules"))

    #def get_object_id(self, obj):
    #    return obj["uuid"]

    #def get_object_display(self, obj):
    #    return obj["name"]

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        row_actions = (Firewall,)

class FirewallTable(tables.DataTable):
    gateway_ip = tables.Column("gateway_ip",
                                verbose_name=_("Gateway Address"))
    gateway_port = tables.Column("gateway_port",
                                 verbose_name=_("Gateway Port"))
    service_port = tables.Column("service_port",
                                 verbose_name=_("Service Port"))

    #def get_object_id(self, obj):
    #    return '%s_%s' % (obj.instance_id, obj.id)

    def get_object_display(self, datum):
        return "Service Port(%s)" % datum.gateway_port

    class Meta:
        name = "firewalls"
        verbose_name = _("Firewalls")
        table_actions = (DeleteFirewall,)
        row_actions = (DeleteFirewall,)# CreateFirewall)
