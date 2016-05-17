# Copyright (c) 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""The hypervisors admin extension."""

import webob.exc

from nova.api.openstack import extensions
from nova import compute
from nova import exception
from nova.i18n import _
from nova import servicegroup


authorize = extensions.extension_authorizer('compute', 'hypervisors')


class HypervisorsController(object):
    """The Hypervisors API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.host_api = compute.HostAPI()
        self.servicegroup_api = servicegroup.API()
        super(HypervisorsController, self).__init__()
        self.ext_mgr = ext_mgr

    def _view_hypervisor(self, hypervisor, service, detail, servers=None,
                         **kwargs):
        hyp_dict = {
            'id': hypervisor.id,
            'hypervisor_hostname': hypervisor.hypervisor_hostname,
            }

        ext_status_loaded = self.ext_mgr.is_loaded('os-hypervisor-status')
        if ext_status_loaded:
            alive = self.servicegroup_api.service_is_up(service)
            hyp_dict['state'] = 'up' if alive else "down"
            hyp_dict['status'] = (
                'disabled' if service.disabled else 'enabled')

        if detail and not servers:
            fields = ('vcpus', 'memory_mb', 'local_gb', 'vcpus_used',
                      'memory_mb_used', 'local_gb_used',
                      'hypervisor_type', 'hypervisor_version',
                      'free_ram_mb', 'free_disk_gb', 'current_workload',
                      'running_vms', 'cpu_info', 'disk_available_least')
            ext_loaded = self.ext_mgr.is_loaded('os-extended-hypervisors')
            if ext_loaded:
                fields += ('host_ip',)
            for field in fields:
                hyp_dict[field] = hypervisor[field]

            hyp_dict['service'] = {
                'id': service.id,
                'host': hypervisor.host,
                }
            if ext_status_loaded:
                hyp_dict['service'].update(
                    disabled_reason=service.disabled_reason)

        if servers:
            hyp_dict['servers'] = [dict(name=serv['name'], uuid=serv['uuid'])
                                   for serv in servers]

        # Add any additional info
        if kwargs:
            hyp_dict.update(kwargs)

        return hyp_dict

    def index(self, req):
        context = req.environ['nova.context']
        authorize(context)
        compute_nodes = self.host_api.compute_node_get_all(context)
        req.cache_db_compute_nodes(compute_nodes)
        return dict(hypervisors=[self._view_hypervisor(
                                 hyp,
                                 self.host_api.service_get_by_compute_host(
                                     context, hyp.host),
                                 False)
                                 for hyp in compute_nodes])

    def detail(self, req):
        context = req.environ['nova.context']
        authorize(context)
        compute_nodes = self.host_api.compute_node_get_all(context)
        req.cache_db_compute_nodes(compute_nodes)
        return dict(hypervisors=[self._view_hypervisor(
                                 hyp,
                                 self.host_api.service_get_by_compute_host(
                                     context, hyp.host),
                                 True)
                                 for hyp in compute_nodes])

    def show(self, req, id):
        context = req.environ['nova.context']
        authorize(context)
        try:
            hyp = self.host_api.compute_node_get(context, id)
            req.cache_db_compute_node(hyp)
        except (ValueError, exception.ComputeHostNotFound):
            msg = _("Hypervisor with ID '%s' could not be found.") % id
            raise webob.exc.HTTPNotFound(explanation=msg)
        service = self.host_api.service_get_by_compute_host(context, hyp.host)
        return dict(hypervisor=self._view_hypervisor(hyp, service, True))

    def uptime(self, req, id):
        context = req.environ['nova.context']
        authorize(context)
        try:
            hyp = self.host_api.compute_node_get(context, id)
            req.cache_db_compute_node(hyp)
        except (ValueError, exception.ComputeHostNotFound):
            msg = _("Hypervisor with ID '%s' could not be found.") % id
            raise webob.exc.HTTPNotFound(explanation=msg)

        # Get the uptime
        try:
            host = hyp.host
            uptime = self.host_api.get_host_uptime(context, host)
        except NotImplementedError:
            msg = _("Virt driver does not implement uptime function.")
            raise webob.exc.HTTPNotImplemented(explanation=msg)

        service = self.host_api.service_get_by_compute_host(context, host)
        return dict(hypervisor=self._view_hypervisor(hyp, service, False,
                                                     uptime=uptime))

    def search(self, req, id):
        context = req.environ['nova.context']
        authorize(context)
        hypervisors = self.host_api.compute_node_search_by_hypervisor(
                context, id)
        if hypervisors:
            return dict(hypervisors=[self._view_hypervisor(
                                     hyp,
                                     self.host_api.service_get_by_compute_host(
                                         context, hyp.host),
                                     False)
                                     for hyp in hypervisors])
        else:
            msg = _("No hypervisor matching '%s' could be found.") % id
            raise webob.exc.HTTPNotFound(explanation=msg)

    def servers(self, req, id):
        context = req.environ['nova.context']
        authorize(context)
        compute_nodes = self.host_api.compute_node_search_by_hypervisor(
                context, id)
        if not compute_nodes:
            msg = _("No hypervisor matching '%s' could be found.") % id
            raise webob.exc.HTTPNotFound(explanation=msg)
        hypervisors = []
        for compute_node in compute_nodes:
            instances = self.host_api.instance_get_all_by_host(context,
                    compute_node.host)
            service = self.host_api.service_get_by_compute_host(
                context, compute_node.host)
            hyp = self._view_hypervisor(compute_node, service, False,
                                        instances)
            hypervisors.append(hyp)
        return dict(hypervisors=hypervisors)

    def statistics(self, req):
        context = req.environ['nova.context']
        authorize(context)
        stats = self.host_api.compute_node_statistics(context)
        return dict(hypervisor_statistics=stats)


class Hypervisors(extensions.ExtensionDescriptor):
    """Admin-only hypervisor administration."""

    name = "Hypervisors"
    alias = "os-hypervisors"
    namespace = "http://docs.openstack.org/compute/ext/hypervisors/api/v1.1"
    updated = "2012-06-21T00:00:00Z"

    def get_resources(self):
        resources = [extensions.ResourceExtension('os-hypervisors',
                HypervisorsController(self.ext_mgr),
                collection_actions={'detail': 'GET',
                                    'statistics': 'GET'},
                member_actions={'uptime': 'GET',
                                'search': 'GET',
                                'servers': 'GET'})]

        return resources
