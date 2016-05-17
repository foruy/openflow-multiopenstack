import logging
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon import forms
from horizon import exceptions
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.network_edges.tables \
    import InstancesTable
from openstack_dashboard.dashboards.project.network_edges.tables \
    import FirewallTable
from openstack_dashboard.dashboards.project.network_edges.forms \
    import FirewallForm

LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = InstancesTable
    template_name = 'project/network_edges/index.html'

    def get_data(self):
        instances = api.proxy.server_list(self.request)

        gateways = dict((gateway.hostname, gateway.vext_ip)
            for gateway in api.proxy.gateway_list(self.request))

        for instance in instances:
            instance.firewall = api.proxy.firewall_get(self.request, instance.id)
            for firewall in instance.firewall:
                firewall.gateway_ip = gateways.get(firewall.hostname)

        return instances

class UpdateView(tables.DataTableView, forms.ModalFormView):
    table_class = FirewallTable
    form_class = FirewallForm
    template_name = 'project/network_edges/update.html'
    success_url = reverse_lazy("horizon:project:network_edges:index")

    def _object_get(self, request):
        if not hasattr(self, 'gateways'):
            self.gateways = api.proxy.gateway_get(request, self.kwargs['id'])
        return self.gateways

    def get_data(self):
        firewalls = api.proxy.firewall_get(self.request, self.kwargs['id'])

        gateways = dict((gateway.hostname, gateway.vext_ip)
            for gateway in api.proxy.gateway_list(self.request))
            #for gateway in self._object_get(self.request))

        for firewall in firewalls:
            firewall.gateway_ip = gateways.get(firewall.hostname)

        return firewalls

    def get_initial(self):
        instance = api.proxy.server_get(self.request, self.kwargs['id'])
        gateways = self._object_get(self.request)

        return {'instance': instance, 'gateways': gateways}

    @memoized.memoized_method
    def get_form(self):
        form_class = self.get_form_class()
        return super(UpdateView, self).get_form(form_class)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        if self.request.is_ajax():
            context['hide'] = True
        context['instance_id'] = self.kwargs['id']
        return context

    #def get(self, request, *args, **kwargs):
    #    # Table action handling
    #    handled = self.construct_tables()
    #    if handled:
    #        return handled
    #    return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)
