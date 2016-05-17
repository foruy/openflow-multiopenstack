import os
from webob import exc

from oslo.config import cfg

import nova.context
from nova import objects
from nova import conductor
from nova.objects import base as obj_base
from nova.compute.rpcapi import ComputeAPI

CONF = cfg.CONF
CONF.import_opt('host', 'nova.netconf')
CONF.register_opt(cfg.IntOpt('idc_id',
                             default=os.environ.get('idc_id', 0)))

class FlowController(object):
    def __init__(self, *args, **kwargs):
        self.compute_api = ComputeAPI()
        self.conductor_api = conductor.API()
        self.context = nova.context.get_admin_context()

    def _from_body(self, body, key):
        if not body:
            raise exc.HTTPUnprocessableEntity()
        value = body.get(key, None)
        if value is None:
            raise exc.HTTPUnprocessableEntity()
        return value

    def instance_get_all_by_filters(self, req, body):
        filters = self._from_body(body, 'filters')
        instances = []
        inst_models = objects.InstanceList.get_by_filters(
                self.context, filters=filters)
        for inst_model in inst_models:
            instances.append(obj_base.obj_to_primitive(inst_model))
        return {'instances': instances}

    def gateway_list(self, req):
        gateways = []
        compute_nodes = self.conductor_api.service_get_all_by_topic(
                self.context, 'compute')
        for node in compute_nodes:
            service = self.compute_api.gateway_get(self.context, node['host'])
            service['hostname'] = node['host']
            service['idc_id'] = CONF.idc_id
            gateways.append(service)

        return {'gateways': gateways}
