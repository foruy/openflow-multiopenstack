"""
Views for managing instances.
"""
import json
from django import shortcuts
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import workflows

from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.project.instances \
    import workflows as project_workflows
from openstack_dashboard.dashboards.project.instances \
    import forms as project_forms

from openstack_dashboard import api
from openstack_dashboard import validators

import logging
LOG=logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = project_tables.InstancesTable
    template_name = 'project/instances/index.html'

    def get_data(self):
        zones = []
        image_dict = {}
        instances = []
        try:
            instances = api.proxy.server_list(self.request)
        except:
            servers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instances.'),
                              ignore=True)

        try:
            for zone in api.proxy.availability_zone_list(self.request, True):
                zones.append(zone)
                try:
                    images = SortedDict([(image.imageid, image) for image in
                         image_utils.get_available_images(self.request, zone.id)])
                except:
                    images = {}
                image_dict.update(images)
        except:
            zones = []
            exceptions.handle(request, _('Unable to retrieve zones.'), ignore=True)

        zone_dict = SortedDict([(zone.id, zone.name) for zone in zones])

        gateway_dict = SortedDict([(g.hostname, g.vext_ip)
                                  for g in api.proxy.gateway_list(self.request)])
        for instance in instances:
            if zone_dict.has_key(instance.zone_id):
                instance.zone_id = zone_dict[instance.zone_id]

            image = image_dict.get(instance.image_id)
            if image:
                instance.image_name = image.name
                if image.container_format == 'docker':
                    instance.image_name += '(Container)'
                else:
                    instance.image_name += '(VM)'
            else:
                instance.image_name = instance.image_id

            firewall = [(gateway_dict.get(f.hostname), f.gateway_port) for f in
                        api.proxy.firewall_get(self.request, instance.id)]
            if firewall:
                instance.gateway = '%s:%s' % firewall[0]
            else:
                instance.gateway= ''

        return instances

class ChoiceView(forms.ModalFormView):
    form_class = project_forms.ChoiceForm
    template_name = 'project/instances/choice.html'

    def get_context_data(self, **kwargs):
        context = super(ChoiceView, self).get_context_data(**kwargs)
        zones = []
        for zone in api.proxy.availability_zone_list(self.request):
            try:
                limit = api.proxy.project_absolute_limits(self.request, zone.id)
                if limit.maxTotalInstances - limit.totalInstancesUsed  <= 0:
                    zone.disabled = True
                else:
                    zone.disabled = zone.disabled
            except:
                zone.disabled = True
            zones.append(zone)
        context['zones'] = zones
        return context

class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchInstance

    #def get_initial(self):
    #    initial = super(LaunchInstanceView, self).get_initial()
    #    initial['zone_id'] = self.kwargs["id"]
    #    return initial

def network(request):
    status = 200
    if request.method == 'POST':
        address = request.POST.get('address')
        if address:
            try:
                validators.validate_address(address)
                api.proxy.server_network(request, address)
            except:
                status = 400
        return HttpResponse(status=status)
    else:
        return shortcuts.redirect(reverse("horizon:project:instances:index"))

def network_type(request):
    #net_type = api.proxy.get_last_network_type(request)
    netype = request.session.get('netype', 1)
    return HttpResponse(json.dumps({'net_type': netype}),
                        content_type='application/json')

def quotas(request):
    limits = api.proxy.user_absolute_limits(request)

    if limits.maxTotalInstances <= limits.totalInstancesUsed:
        return HttpResponse(_("Quota exceeded."), status=400)

    quota = {'total': limits.maxTotalInstances, 'used': limits.totalInstancesUsed}

    return HttpResponse(json.dumps(quota), content_type='application/json')
