import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _
from daoliproxy import utils

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The zone API controller.
    """

    def list(self, req):
        context = req.environ['proxy.context']
        detail = req.GET.get('detail', False)

        zone_list = self.db.zone_get_all(context, disabled=detail)

        if not detail:
            avail_zone = context.service_catalog
            zones = [zone for zone in zone_list
                        if avail_zone.has_key(zone.id)]
        else:
            zones = zone_list

        return {"zones": zones}

    def get(self, req, id):
        context = req.environ['proxy.context']
        zone = self.db.zone_get(context, id)
        return {"zone": zone}

    def _sync_user_thread(self, context, zone):
        for user in self.db.user_get_all(context):
            if user.username in utils.USER_FILTERS:
                continue
            try:
                self._register_thread(context, zone, user)
            except Exception as e:
                LOG.error(e.message)

    def _rebuild(self, req, body, checked=False):
        zone = self._from_body(body, 'zone')
        context = req.environ['proxy.context']

        if not zone.has_key('idc_id'):
            zone['idc_id'] = CONF.idc_id

        if self.db.zone_exists(context, auth_url=zone['auth_url']):
            msg = _("Zone (%s) already exists") % zone['auth_url']
            raise exc.HTTPConflict(explanation=msg)

        try:
            user = self.db.role_get_by_name(context, context.user_id)
        except exception.AdminRequired as e:
            raise exc.HTTPForbidden(explanation=e)

        if checked and zone['idc_id'] != CONF.idc_id:
            return self.proxy_method('zone_create_proxy',
                    context, zone['idc_id'], body)

        zone_ref = self.db.zone_create(context, zone)

        try:
            self._authenticate(context, user, zone_ref)
        except:
            self.db.zone_delete(context, zone_ref.id)
            raise

        self.add_thread(self._sync_user_thread, context, zone_ref)

        return {'zone': zone_ref}

    def delete(self, req, id):
        context = req.environ['proxy.context']
        self.db.network_delete(context, zone_id=id)
        self.db.gateway_delete(context, zone_id=id)
        self.db.flavor_delete(context, zone_id=id)
        self.db.image_delete(context, zone_id=id)
        self.db.zone_delete(context, id)
        return webob.Response(status_int=202)

def create_resource():
    return wsgi.Resource(Controller())
