# Copyright 2011 OpenStack Foundation
# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 Grid Dynamics
# Copyright 2011 Eldar Nugaev, Kirill Shileev, Ilya Alekseyev
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

from oslo_log import log as logging
from oslo_utils import uuidutils
import webob

from nova.api.openstack import common
from nova.api.openstack.compute.schemas.v3 import floating_ips
from nova.api.openstack import extensions
from nova.api.openstack import wsgi
from nova.api import validation
from nova import compute
from nova.compute import utils as compute_utils
from nova import exception
from nova.i18n import _
from nova.i18n import _LW
from nova import network


LOG = logging.getLogger(__name__)
ALIAS = 'os-floating-ips'
authorize = extensions.os_compute_authorizer(ALIAS)


def _translate_floating_ip_view(floating_ip):
    result = {
        'id': floating_ip['id'],
        'ip': floating_ip['address'],
        'pool': floating_ip['pool'],
    }
    try:
        result['fixed_ip'] = floating_ip['fixed_ip']['address']
    except (TypeError, KeyError, AttributeError):
        result['fixed_ip'] = None
    try:
        result['instance_id'] = floating_ip['fixed_ip']['instance_uuid']
    except (TypeError, KeyError, AttributeError):
        result['instance_id'] = None
    return {'floating_ip': result}


def _translate_floating_ips_view(floating_ips):
    return {'floating_ips': [_translate_floating_ip_view(ip)['floating_ip']
                             for ip in floating_ips]}


def get_instance_by_floating_ip_addr(self, context, address):
    try:
        instance_id =\
            self.network_api.get_instance_id_by_floating_address(
                context, address)
    except exception.FloatingIpNotFoundForAddress as ex:
        raise webob.exc.HTTPNotFound(explanation=ex.format_message())
    except exception.FloatingIpMultipleFoundForAddress as ex:
        raise webob.exc.HTTPConflict(explanation=ex.format_message())

    if instance_id:
        return common.get_instance(self.compute_api, context, instance_id)


def disassociate_floating_ip(self, context, instance, address):
    try:
        self.network_api.disassociate_floating_ip(context, instance, address)
    except exception.Forbidden:
        raise webob.exc.HTTPForbidden()
    except exception.CannotDisassociateAutoAssignedFloatingIP:
        msg = _('Cannot disassociate auto assigned floating ip')
        raise webob.exc.HTTPForbidden(explanation=msg)


class FloatingIPController(object):
    """The Floating IPs API controller for the OpenStack API."""

    def __init__(self):
        self.compute_api = compute.API(skip_policy_check=True)
        self.network_api = network.API(skip_policy_check=True)
        super(FloatingIPController, self).__init__()

    @extensions.expected_errors((400, 404))
    def show(self, req, id):
        """Return data about the given floating ip."""
        context = req.environ['nova.context']
        authorize(context)

        try:
            floating_ip = self.network_api.get_floating_ip(context, id)
        except (exception.NotFound, exception.FloatingIpNotFound):
            msg = _("Floating ip not found for id %s") % id
            raise webob.exc.HTTPNotFound(explanation=msg)
        except exception.InvalidID as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        return _translate_floating_ip_view(floating_ip)

    @extensions.expected_errors(())
    def index(self, req):
        """Return a list of floating ips allocated to a project."""
        context = req.environ['nova.context']
        authorize(context)

        floating_ips = self.network_api.get_floating_ips_by_project(context)

        return _translate_floating_ips_view(floating_ips)

    @extensions.expected_errors((403, 404))
    def create(self, req, body=None):
        context = req.environ['nova.context']
        authorize(context)

        pool = None
        if body and 'pool' in body:
            pool = body['pool']
        try:
            address = self.network_api.allocate_floating_ip(context, pool)
            ip = self.network_api.get_floating_ip_by_address(context, address)
        except exception.NoMoreFloatingIps:
            if pool:
                msg = _("No more floating ips in pool %s.") % pool
            else:
                msg = _("No more floating ips available.")
            raise webob.exc.HTTPNotFound(explanation=msg)
        except exception.FloatingIpLimitExceeded:
            if pool:
                msg = _("IP allocation over quota in pool %s.") % pool
            else:
                msg = _("IP allocation over quota.")
            raise webob.exc.HTTPForbidden(explanation=msg)
        except exception.FloatingIpPoolNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return _translate_floating_ip_view(ip)

    @wsgi.response(202)
    @extensions.expected_errors((400, 403, 404, 409))
    def delete(self, req, id):
        context = req.environ['nova.context']
        authorize(context)

        # get the floating ip object
        try:
            floating_ip = self.network_api.get_floating_ip(context, id)
        except (exception.NotFound, exception.FloatingIpNotFound):
            msg = _("Floating ip not found for id %s") % id
            raise webob.exc.HTTPNotFound(explanation=msg)
        except exception.InvalidID as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        address = floating_ip['address']

        # get the associated instance object (if any)
        instance = get_instance_by_floating_ip_addr(self, context, address)
        try:
            self.network_api.disassociate_and_release_floating_ip(
                context, instance, floating_ip)
        except exception.Forbidden:
            raise webob.exc.HTTPForbidden()
        except exception.CannotDisassociateAutoAssignedFloatingIP:
            msg = _('Cannot disassociate auto assigned floating ip')
            raise webob.exc.HTTPForbidden(explanation=msg)


class FloatingIPActionController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(FloatingIPActionController, self).__init__(*args, **kwargs)
        self.compute_api = compute.API(skip_policy_check=True)
        self.network_api = network.API(skip_policy_check=True)

    @extensions.expected_errors((400, 403, 404))
    @wsgi.action('addFloatingIp')
    @validation.schema(floating_ips.add_floating_ip)
    def _add_floating_ip(self, req, id, body):
        """Associate floating_ip to an instance."""
        context = req.environ['nova.context']
        authorize(context)

        address = body['addFloatingIp']['address']

        instance = common.get_instance(self.compute_api, context, id)
        cached_nwinfo = compute_utils.get_nw_info_for_instance(instance)
        if not cached_nwinfo:
            msg = _('No nw_info cache associated with instance')
            raise webob.exc.HTTPBadRequest(explanation=msg)

        fixed_ips = cached_nwinfo.fixed_ips()
        if not fixed_ips:
            msg = _('No fixed ips associated to instance')
            raise webob.exc.HTTPBadRequest(explanation=msg)

        fixed_address = None
        if 'fixed_address' in body['addFloatingIp']:
            fixed_address = body['addFloatingIp']['fixed_address']
            for fixed in fixed_ips:
                if fixed['address'] == fixed_address:
                    break
            else:
                msg = _('Specified fixed address not assigned to instance')
                raise webob.exc.HTTPBadRequest(explanation=msg)

        if not fixed_address:
            fixed_address = fixed_ips[0]['address']
            if len(fixed_ips) > 1:
                LOG.warning(_LW('multiple fixed_ips exist, using the first: '
                                '%s'), fixed_address)

        try:
            self.network_api.associate_floating_ip(context, instance,
                                  floating_address=address,
                                  fixed_address=fixed_address)
        except exception.FloatingIpAssociated:
            msg = _('floating ip is already associated')
            raise webob.exc.HTTPBadRequest(explanation=msg)
        except exception.NoFloatingIpInterface:
            msg = _('l3driver call to add floating ip failed')
            raise webob.exc.HTTPBadRequest(explanation=msg)
        except exception.FloatingIpNotFoundForAddress:
            msg = _('floating ip not found')
            raise webob.exc.HTTPNotFound(explanation=msg)
        except exception.Forbidden as e:
            raise webob.exc.HTTPForbidden(explanation=e.format_message())
        except Exception as e:
            msg = _('Unable to associate floating ip %(address)s to '
                    'fixed ip %(fixed_address)s for instance %(id)s. '
                    'Error: %(error)s') % (
                    {'address': address, 'fixed_address': fixed_address,
                     'id': id, 'error': e})
            LOG.exception(msg)
            raise webob.exc.HTTPBadRequest(explanation=msg)

        return webob.Response(status_int=202)

    @extensions.expected_errors((400, 403, 404, 409))
    @wsgi.action('removeFloatingIp')
    @validation.schema(floating_ips.remove_floating_ip)
    def _remove_floating_ip(self, req, id, body):
        """Dissociate floating_ip from an instance."""
        context = req.environ['nova.context']
        authorize(context)

        address = body['removeFloatingIp']['address']

        # get the floating ip object
        try:
            floating_ip = self.network_api.get_floating_ip_by_address(context,
                                                                      address)
        except exception.FloatingIpNotFoundForAddress:
            msg = _("floating ip not found")
            raise webob.exc.HTTPNotFound(explanation=msg)

        # get the associated instance object (if any)
        instance = get_instance_by_floating_ip_addr(self, context, address)

        # disassociate if associated
        if (instance and
            floating_ip.get('fixed_ip_id') and
            (uuidutils.is_uuid_like(id) and
             [instance.uuid == id] or
             [instance.id == id])[0]):
            try:
                disassociate_floating_ip(self, context, instance, address)
            except exception.FloatingIpNotAssociated:
                msg = _('Floating ip is not associated')
                raise webob.exc.HTTPBadRequest(explanation=msg)
            return webob.Response(status_int=202)
        else:
            msg = _("Floating ip %(address)s is not associated with instance "
                    "%(id)s.") % {'address': address, 'id': id}
            raise webob.exc.HTTPConflict(explanation=msg)


class FloatingIps(extensions.V3APIExtensionBase):
    """Floating IPs support."""

    name = "FloatingIps"
    alias = ALIAS
    version = 1

    def get_resources(self):
        resource = [extensions.ResourceExtension(ALIAS,
                                FloatingIPController())]
        return resource

    def get_controller_extensions(self):
        controller = FloatingIPActionController()
        extension = extensions.ControllerExtension(self, 'servers', controller)
        return [extension]
