"""
Views for managing instances.
"""
import logging

from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from horizon import exceptions
from horizon import tables
from horizon.views import APIView

from openstack_dashboard.dashboards.project.images \
    import utils as image_utils
from openstack_dashboard.dashboards.project.monitors \
    import tables as project_tables

from openstack_dashboard import api

LOG=logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = project_tables.InstanceTable
    template_name = 'project/monitors/index.html'

#    def get_data(self):
#        instances = []
#
#        try:
#            instances = api.proxy.server_list(self.request)
#        except:
#            servers = []
#            exceptions.handle(self.request,
#                              _('Unable to retrieve instances.'),
#                              ignore=True)
#        return instances

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
                    images = SortedDict([(image.id, image) for image in
                         image_utils.get_available_images(self.request, zone.id)])
                except:
                    images = {}
                image_dict.update(images)
        except:
            zones = []
            exceptions.handle(self.request, _('Unable to retrieve zones.'), ignore=True)

#        zone_dict = SortedDict([(zone.id, zone.name) for zone in zones])
#
#        gateway_dict = SortedDict([(g.hostname, g.ext_ip)
#                                  for g in api.proxy.gateway_list(self.request)])
        for instance in instances:
#            if zone_dict.has_key(instance.availability_zone):
#                instance.availability_zone = zone_dict[instance.availability_zone]

            image = image_dict.get(instance.image)
            if image:
                instance.image_name = image.name
                if image.container_format == 'docker':
                    instance.instance_type = 'Docker'
                    instance.image_name += '(Container)'
                else:
                    instance.instance_type = 'VM'
                    instance.image_name += '(VM)'
            else:
                instance.image_name = instance.image

#            firewall = [(gateway_dict.get(f.hostname), f.gateway_port) for f in
#                        api.proxy.firewall_get(self.request, instance.id)]
#            if firewall:
#                instance.gateway = '%s:%s' % firewall[0]
#            else:
#                instance.gateway= ''

        return instances

class DetailView(APIView):
    template_name = "project/monitors/detail.html"

    def get_data(self, request, context, *args, **kwargs):
        instance_id = self.kwargs["instance_id"]
        monitor = api.proxy.get_monitor(request, instance_id)
        context['monitor_url'] = monitor.monitor_url
        return context
