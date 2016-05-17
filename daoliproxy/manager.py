from eventlet import greenthread

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy import context
from daoliproxy.db import base
from daoliproxy.openstack.common import periodic_task
from daoliproxy import utils

from proxyclient.client import HTTPClient


agent_opts = [
    cfg.IntOpt('agent_port', default=65535, help='The compute agent port')
]

CONF = cfg.CONF
CONF.register_opts(agent_opts)

LOG = logging.getLogger(__name__)


class Manager(base.Base, periodic_task.PeriodicTasks):

    def periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        return self.run_periodic_tasks(context.get_admin_context(),
                                       raise_on_error=raise_on_error)

    def init_host(self):
        """Hook to do additional manager initialization when one requests
        the service be started.  This is called before any service record
        is created.

        Child classes should override this method.
        """
        pass

    def cleanup_host(self):
        """Hook to do cleanup work when the service shuts down.

        Child classes should override this method.
        """
        pass

    def pre_start_hook(self):
        """Hook to provide the manager the ability to do additional
        start-up work before any RPC queues/consumers are created. This is
        called after other initialization has succeeded and a service
        record is created.

        Child classes should override this method.
        """
        pass

    def post_start_hook(self):
        """Hook to provide the manager the ability to do additional
        start-up work immediately after a service creates RPC consumers
        and starts 'running'.

        Child classes should override this method.
        """
        pass

class ProxyManager(Manager):

    def __init__(self, db_driver=None):
        super(ProxyManager, self).__init__(db_driver=db_driver)
        self.client = HTTPClient(http_log_debug=CONF.debug)

    @periodic_task.periodic_task
    def _sync_db(self, context):
        """Ensure that local instances sync status with remote."""
        for zone in self.db.zone_get_all(context, idc_id=CONF.idc_id):
            self.client.set_management_url(utils.replace_url(
                    zone.auth_url, port=CONF.agent_port, paht=''))
            data = {'filters': {'sort_key': 'created_at',
                                'sort_dir': 'desc',
                                'deleted': False}}
            try:
                resp, body = self.client.post('/instances', body=data)
                if zone.disabled:
                    self.db.zone_update(context, zone.id, {'disabled': False})
            except Exception as e:
                LOG.error(e.message)
                if not zone.disabled:
                    self.db.zone_update(context, zone.id, {'disabled': True})
                continue

            instances = dict((inst['uuid'], inst) for inst in body['instances'])
            self._sync_instance(context, zone.id, instances)
            greenthread.sleep(0)

    def _sync_instance(self, context, id, instances):
        for server in self.db.server_get_by_zone(context, id):
            inst = instances.get(server.id)
            if inst and (server['status'] != inst['vm_state'] or \
                    server['power_state'] != inst['power_state']):
                LOG.info('Changing Instance Status [vm_state:power_state] from '
                         '[%s:%s] to [%s:%s]' % (
                         server['status'], server['power_state'],
                         inst['vm_state'], inst['power_state']))
                values = {'status': inst['vm_state'],
                          'power_state': inst['power_state']}
                self.db.server_update(context, server['id'], values)
