# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""
Handles all requests relating to volumes + cinder.
"""

import copy
import sys

from cinderclient import client as cinder_client
from cinderclient import exceptions as cinder_exception
from cinderclient.v1 import client as v1_client
from keystoneclient import exceptions as keystone_exception
from keystoneclient import session
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import strutils
import six
import six.moves.urllib.parse as urlparse

from nova import availability_zones as az
from nova import exception
from nova.i18n import _
from nova.i18n import _LW

cinder_opts = [
    cfg.StrOpt('catalog_info',
            default='volumev2:cinderv2:publicURL',
            help='Info to match when looking for cinder in the service '
                 'catalog. Format is: separated values of the form: '
                 '<service_type>:<service_name>:<endpoint_type>'),
    cfg.StrOpt('endpoint_template',
               help='Override service catalog lookup with template for cinder '
                    'endpoint e.g. http://localhost:8776/v1/%(project_id)s'),
    cfg.StrOpt('os_region_name',
               help='Region name of this node'),
    cfg.IntOpt('http_retries',
               default=3,
               help='Number of cinderclient retries on failed http calls'),
    cfg.BoolOpt('cross_az_attach',
                default=True,
                help='Allow attach between instance and volume in different '
                     'availability zones.'),
]

CONF = cfg.CONF
CINDER_OPT_GROUP = 'cinder'

# cinder_opts options in the DEFAULT group were deprecated in Juno
CONF.register_opts(cinder_opts, group=CINDER_OPT_GROUP)


deprecated = {'timeout': [cfg.DeprecatedOpt('http_timeout',
                                            group=CINDER_OPT_GROUP)],
              'cafile': [cfg.DeprecatedOpt('ca_certificates_file',
                                           group=CINDER_OPT_GROUP)],
              'insecure': [cfg.DeprecatedOpt('api_insecure',
                                             group=CINDER_OPT_GROUP)]}

session.Session.register_conf_options(CONF,
                                      CINDER_OPT_GROUP,
                                      deprecated_opts=deprecated)

LOG = logging.getLogger(__name__)

_SESSION = None
_V1_ERROR_RAISED = False


def reset_globals():
    """Testing method to reset globals.
    """
    global _SESSION
    _SESSION = None


def cinderclient(context):
    global _SESSION
    global _V1_ERROR_RAISED

    if not _SESSION:
        _SESSION = session.Session.load_from_conf_options(CONF,
                                                          CINDER_OPT_GROUP)

    url = None
    endpoint_override = None
    version = None

    auth = context.get_auth_plugin()
    service_type, service_name, interface = CONF.cinder.catalog_info.split(':')

    service_parameters = {'service_type': service_type,
                          'service_name': service_name,
                          'interface': interface,
                          'region_name': CONF.cinder.os_region_name}

    if CONF.cinder.endpoint_template:
        url = CONF.cinder.endpoint_template % context.to_dict()
        endpoint_override = url
    else:
        url = _SESSION.get_endpoint(auth, **service_parameters)

    # TODO(jamielennox): This should be using proper version discovery from
    # the cinder service rather than just inspecting the URL for certain string
    # values.
    version = get_cinder_client_version(url)

    if version == '1' and not _V1_ERROR_RAISED:
        msg = _LW('Cinder V1 API is deprecated as of the Juno '
                  'release, and Nova is still configured to use it. '
                  'Enable the V2 API in Cinder and set '
                  'cinder_catalog_info in nova.conf to use it.')
        LOG.warn(msg)
        _V1_ERROR_RAISED = True

    return cinder_client.Client(version,
                                session=_SESSION,
                                auth=auth,
                                endpoint_override=endpoint_override,
                                connect_retries=CONF.cinder.http_retries,
                                **service_parameters)


def _untranslate_volume_summary_view(context, vol):
    """Maps keys for volumes summary view."""
    d = {}
    d['id'] = vol.id
    d['status'] = vol.status
    d['size'] = vol.size
    d['availability_zone'] = vol.availability_zone
    d['created_at'] = vol.created_at

    # TODO(jdg): The calling code expects attach_time and
    #            mountpoint to be set. When the calling
    #            code is more defensive this can be
    #            removed.
    d['attach_time'] = ""
    d['mountpoint'] = ""

    if vol.attachments:
        att = vol.attachments[0]
        d['attach_status'] = 'attached'
        d['instance_uuid'] = att['server_id']
        d['mountpoint'] = att['device']
    else:
        d['attach_status'] = 'detached'
    # NOTE(dzyu) volume(cinder) v2 API uses 'name' instead of 'display_name',
    # and use 'description' instead of 'display_description' for volume.
    if hasattr(vol, 'display_name'):
        d['display_name'] = vol.display_name
        d['display_description'] = vol.display_description
    else:
        d['display_name'] = vol.name
        d['display_description'] = vol.description
    # TODO(jdg): Information may be lost in this translation
    d['volume_type_id'] = vol.volume_type
    d['snapshot_id'] = vol.snapshot_id
    d['bootable'] = strutils.bool_from_string(vol.bootable)
    d['volume_metadata'] = {}
    for key, value in vol.metadata.items():
        d['volume_metadata'][key] = value

    if hasattr(vol, 'volume_image_metadata'):
        d['volume_image_metadata'] = copy.deepcopy(vol.volume_image_metadata)

    return d


def _untranslate_snapshot_summary_view(context, snapshot):
    """Maps keys for snapshots summary view."""
    d = {}

    d['id'] = snapshot.id
    d['status'] = snapshot.status
    d['progress'] = snapshot.progress
    d['size'] = snapshot.size
    d['created_at'] = snapshot.created_at

    # NOTE(dzyu) volume(cinder) v2 API uses 'name' instead of 'display_name',
    # 'description' instead of 'display_description' for snapshot.
    if hasattr(snapshot, 'display_name'):
        d['display_name'] = snapshot.display_name
        d['display_description'] = snapshot.display_description
    else:
        d['display_name'] = snapshot.name
        d['display_description'] = snapshot.description

    d['volume_id'] = snapshot.volume_id
    d['project_id'] = snapshot.project_id
    d['volume_size'] = snapshot.size

    return d


def translate_volume_exception(method):
    """Transforms the exception for the volume but keeps its traceback intact.
    """
    def wrapper(self, ctx, volume_id, *args, **kwargs):
        try:
            res = method(self, ctx, volume_id, *args, **kwargs)
        except (cinder_exception.ClientException,
                keystone_exception.ClientException):
            exc_type, exc_value, exc_trace = sys.exc_info()
            if isinstance(exc_value, (keystone_exception.NotFound,
                                      cinder_exception.NotFound)):
                exc_value = exception.VolumeNotFound(volume_id=volume_id)
            elif isinstance(exc_value, (keystone_exception.BadRequest,
                                        cinder_exception.BadRequest)):
                exc_value = exception.InvalidInput(
                    reason=six.text_type(exc_value))
            raise exc_value, None, exc_trace
        except (cinder_exception.ConnectionError,
                keystone_exception.ConnectionError):
            exc_type, exc_value, exc_trace = sys.exc_info()
            exc_value = exception.CinderConnectionFailed(
                reason=six.text_type(exc_value))
            raise exc_value, None, exc_trace
        return res
    return wrapper


def translate_snapshot_exception(method):
    """Transforms the exception for the snapshot but keeps its traceback
       intact.
    """
    def wrapper(self, ctx, snapshot_id, *args, **kwargs):
        try:
            res = method(self, ctx, snapshot_id, *args, **kwargs)
        except (cinder_exception.ClientException,
                keystone_exception.ClientException):
            exc_type, exc_value, exc_trace = sys.exc_info()
            if isinstance(exc_value, (keystone_exception.NotFound,
                                      cinder_exception.NotFound)):
                exc_value = exception.SnapshotNotFound(snapshot_id=snapshot_id)
            raise exc_value, None, exc_trace
        except (cinder_exception.ConnectionError,
                keystone_exception.ConnectionError):
            exc_type, exc_value, exc_trace = sys.exc_info()
            reason = six.text_type(exc_value)
            exc_value = exception.CinderConnectionFailed(reason=reason)
            raise exc_value, None, exc_trace
        return res
    return wrapper


def get_cinder_client_version(url):
    """Parse cinder client version by endpoint url.

    :param url: URL for cinder.
    :return: str value(1 or 2).
    """
    # FIXME(jamielennox): Use cinder_client.get_volume_api_from_url when
    # bug #1386232 is fixed.
    valid_versions = ['v1', 'v2']
    scheme, netloc, path, query, frag = urlparse.urlsplit(url)
    components = path.split("/")

    for version in valid_versions:
        if version in components:
            return version[1:]

    msg = "Invalid client version '%s'. must be one of: %s" % (
        (version, ', '.join(valid_versions)))
    raise cinder_exception.UnsupportedVersion(msg)


class API(object):
    """API for interacting with the volume manager."""

    @translate_volume_exception
    def get(self, context, volume_id):
        item = cinderclient(context).volumes.get(volume_id)
        return _untranslate_volume_summary_view(context, item)

    def get_all(self, context, search_opts=None):
        search_opts = search_opts or {}
        items = cinderclient(context).volumes.list(detailed=True,
                                                   search_opts=search_opts)

        rval = []

        for item in items:
            rval.append(_untranslate_volume_summary_view(context, item))

        return rval

    def check_attached(self, context, volume):
        if volume['status'] != "in-use":
            msg = _("volume '%(vol)s' status must be 'in-use'. Currently in "
                    "'%(status)s' status") % {"vol": volume['id'],
                                              "status": volume['status']}
            raise exception.InvalidVolume(reason=msg)

    def check_attach(self, context, volume, instance=None):
        # TODO(vish): abstract status checking?
        if volume['status'] != "available":
            msg = _("volume '%(vol)s' status must be 'available'. Currently "
                    "in '%(status)s'") % {'vol': volume['id'],
                                          'status': volume['status']}
            raise exception.InvalidVolume(reason=msg)
        if volume['attach_status'] == "attached":
            msg = _("volume %s already attached") % volume['id']
            raise exception.InvalidVolume(reason=msg)
        if instance and not CONF.cinder.cross_az_attach:
            # NOTE(sorrison): If instance is on a host we match against it's AZ
            #                 else we check the intended AZ
            if instance.get('host'):
                instance_az = az.get_instance_availability_zone(
                    context, instance)
            else:
                instance_az = instance['availability_zone']
            if instance_az != volume['availability_zone']:
                msg = _("Instance %(instance)s and volume %(vol)s are not in "
                        "the same availability_zone. Instance is in "
                        "%(ins_zone)s. Volume is in %(vol_zone)s") % {
                            "instance": instance['id'],
                            "vol": volume['id'],
                            'ins_zone': instance_az,
                            'vol_zone': volume['availability_zone']}
                raise exception.InvalidVolume(reason=msg)

    def check_detach(self, context, volume):
        # TODO(vish): abstract status checking?
        if volume['status'] == "available":
            msg = _("volume %s already detached") % volume['id']
            raise exception.InvalidVolume(reason=msg)

    @translate_volume_exception
    def reserve_volume(self, context, volume_id):
        cinderclient(context).volumes.reserve(volume_id)

    @translate_volume_exception
    def unreserve_volume(self, context, volume_id):
        cinderclient(context).volumes.unreserve(volume_id)

    @translate_volume_exception
    def begin_detaching(self, context, volume_id):
        cinderclient(context).volumes.begin_detaching(volume_id)

    @translate_volume_exception
    def roll_detaching(self, context, volume_id):
        cinderclient(context).volumes.roll_detaching(volume_id)

    @translate_volume_exception
    def attach(self, context, volume_id, instance_uuid, mountpoint, mode='rw'):
        cinderclient(context).volumes.attach(volume_id, instance_uuid,
                                             mountpoint, mode=mode)

    @translate_volume_exception
    def detach(self, context, volume_id):
        cinderclient(context).volumes.detach(volume_id)

    @translate_volume_exception
    def initialize_connection(self, context, volume_id, connector):
        return cinderclient(context).volumes.initialize_connection(volume_id,
                                                                   connector)

    @translate_volume_exception
    def terminate_connection(self, context, volume_id, connector):
        return cinderclient(context).volumes.terminate_connection(volume_id,
                                                                  connector)

    def migrate_volume_completion(self, context, old_volume_id, new_volume_id,
                                  error=False):
        return cinderclient(context).volumes.migrate_volume_completion(
            old_volume_id, new_volume_id, error)

    def create(self, context, size, name, description, snapshot=None,
               image_id=None, volume_type=None, metadata=None,
               availability_zone=None):
        client = cinderclient(context)

        if snapshot is not None:
            snapshot_id = snapshot['id']
        else:
            snapshot_id = None

        kwargs = dict(snapshot_id=snapshot_id,
                      volume_type=volume_type,
                      user_id=context.user_id,
                      project_id=context.project_id,
                      availability_zone=availability_zone,
                      metadata=metadata,
                      imageRef=image_id)

        if isinstance(client, v1_client.Client):
            kwargs['display_name'] = name
            kwargs['display_description'] = description
        else:
            kwargs['name'] = name
            kwargs['description'] = description

        try:
            item = client.volumes.create(size, **kwargs)
            return _untranslate_volume_summary_view(context, item)
        except cinder_exception.OverLimit:
            raise exception.OverQuota(overs='volumes')
        except (cinder_exception.BadRequest,
                keystone_exception.BadRequest) as e:
            raise exception.InvalidInput(reason=e)

    @translate_volume_exception
    def delete(self, context, volume_id):
        cinderclient(context).volumes.delete(volume_id)

    @translate_volume_exception
    def update(self, context, volume_id, fields):
        raise NotImplementedError()

    @translate_snapshot_exception
    def get_snapshot(self, context, snapshot_id):
        item = cinderclient(context).volume_snapshots.get(snapshot_id)
        return _untranslate_snapshot_summary_view(context, item)

    def get_all_snapshots(self, context):
        items = cinderclient(context).volume_snapshots.list(detailed=True)
        rvals = []

        for item in items:
            rvals.append(_untranslate_snapshot_summary_view(context, item))

        return rvals

    @translate_volume_exception
    def create_snapshot(self, context, volume_id, name, description):
        item = cinderclient(context).volume_snapshots.create(volume_id,
                                                             False,
                                                             name,
                                                             description)
        return _untranslate_snapshot_summary_view(context, item)

    @translate_volume_exception
    def create_snapshot_force(self, context, volume_id, name, description):
        item = cinderclient(context).volume_snapshots.create(volume_id,
                                                             True,
                                                             name,
                                                             description)

        return _untranslate_snapshot_summary_view(context, item)

    @translate_snapshot_exception
    def delete_snapshot(self, context, snapshot_id):
        cinderclient(context).volume_snapshots.delete(snapshot_id)

    def get_volume_encryption_metadata(self, context, volume_id):
        return cinderclient(context).volumes.get_encryption_metadata(volume_id)

    @translate_snapshot_exception
    def update_snapshot_status(self, context, snapshot_id, status):
        vs = cinderclient(context).volume_snapshots

        # '90%' here is used to tell Cinder that Nova is done
        # with its portion of the 'creating' state. This can
        # be removed when we are able to split the Cinder states
        # into 'creating' and a separate state of
        # 'creating_in_nova'. (Same for 'deleting' state.)

        vs.update_snapshot_status(
            snapshot_id,
            {'status': status,
             'progress': '90%'}
        )
