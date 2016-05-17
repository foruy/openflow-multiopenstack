import json
import logging
import collections
from netaddr import IPAddress, IPNetwork

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.views.generic import View

from horizon import views
from horizon import exceptions
from horizon.views import APIView

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

#class IndexView(views.HorizonTemplateView):
class IndexView(APIView):
    template_name = 'project/topology/index.html'
    page_title = _("Network Topology")

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context

    def get_data(self, request, context, *args, **kwargs):
        return context

class JSONView(View):

    def _get_servers(self, request):
        try:
            servers = api.proxy.server_list(request)
        except:
            servers = []

        try:
            zones = api.proxy.availability_zone_list(self.request, True)
        except:
            zones = []

        data = []
        zone_dict = dict((zone.id, zone) for zone in zones)

        def _subnet(addr):
            if addr:
                for sid, cidr in self._get_subnets(request):
                    if IPAddress(addr) in IPNetwork(cidr):
                        return sid
            return None

        for server in servers:
            zone = zone_dict.get(server.availability_zone)
            if zone:
                idc = zone.idc_id
            else:
                idc = None
            data.append({'id': server.id,
                         'name': server.name,
                         'status': server.status,
                         'address': server.address,
                         'sub': _subnet(server.address),
                         'idc': idc})

        return data

    def _get_services(self, request):
        return [{'idc_id': 100, 'service': [
                   {'id': 'f4bd6b4a-d585-42aa-9cc7-a1515724b593',
                    'name': 'bj10.daolicloud.com',
                    'address': '1.1.1.1'}]},
                {'idc_id': 200, 'service': [
                   {'id': 'f4bd6b4a-d585-42aa-9cc7-a1515724b594',
                    'name': 'sh03.daolicloud.com',
                    'address': '2.2.2.2'}]},
                {'idc_id': 300, 'service': [
                   {'id': 'f4bd6b4a-d585-42aa-9cc7-a1515724b595',
                    'name': 'sh04.daolicloud.com',
                    'address': '3.3.3.3'}]}]

    def _get_subnets(self, request):
        subnets = getattr(settings, 'SUBNETWORK', [])
        return subnets

    def get(self, request, *args, **kwargs):
        servers = self._get_servers(request)
        services = self._get_services(request)
        subnets = self._get_subnets(request)
        data = {'servers': servers, 'services': services, 'subnets': subnets}
        json_string = json.dumps(data, ensure_ascii=False)
        return HttpResponse(json_string, content_type='text/json')
