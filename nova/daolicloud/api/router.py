from nova.wsgi import Router
from nova.api.openstack import wsgi
from nova.daolicloud.api import APIMapper
from nova.daolicloud.api.controller import FlowController

class APIRouter(Router):
    """WSGI router for daolinat API requests."""
    def __init__(self):
        mapper = APIMapper()

        service = wsgi.Resource(FlowController())

        mapper.connect('/instances',
                controller=service,
                action='instance_get_all_by_filters',
                conditions={"method": ['POST']})

        mapper.connect('/gateways',
                controller=service,
                action='gateway_list',
                conditions={"method": ['GET']})

        super(APIRouter, self).__init__(mapper)
