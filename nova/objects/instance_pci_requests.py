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

from oslo_serialization import jsonutils

from nova import db
from nova.objects import base
from nova.objects import fields
from nova import utils


# TODO(berrange): Remove NovaObjectDictCompat
class InstancePCIRequest(base.NovaObject,
                         base.NovaObjectDictCompat):
    # Version 1.0: Initial version
    # Version 1.1: Add request_id
    VERSION = '1.1'

    fields = {
        'count': fields.IntegerField(),
        'spec': fields.ListOfDictOfNullableStringsField(),
        'alias_name': fields.StringField(nullable=True),
        # A stashed request related to a resize, not current
        'is_new': fields.BooleanField(default=False),
        'request_id': fields.UUIDField(nullable=True),
    }

    def obj_load_attr(self, attr):
        setattr(self, attr, None)

    # NOTE(danms): The dict that this object replaces uses a key of 'new'
    # so we translate it here to our more appropropriately-named 'is_new'.
    # This is not something that affects the obect version, so we could
    # remove this later when all dependent code is fixed.
    @property
    def new(self):
        return self.is_new

    def obj_make_compatible(self, primitive, target_version):
        target_version = utils.convert_version_to_tuple(target_version)
        if target_version < (1, 1) and 'request_id' in primitive:
            del primitive['request_id']


# TODO(berrange): Remove NovaObjectDictCompat
class InstancePCIRequests(base.NovaObject,
                          base.NovaObjectDictCompat):
    # Version 1.0: Initial version
    # Version 1.1: InstancePCIRequest 1.1
    VERSION = '1.1'

    fields = {
        'instance_uuid': fields.UUIDField(),
        'requests': fields.ListOfObjectsField('InstancePCIRequest'),
    }

    obj_relationships = {
        'requests': [('1.0', '1.0'), ('1.1', '1.1')],
    }

    def obj_make_compatible(self, primitive, target_version):
        target_version = utils.convert_version_to_tuple(target_version)
        if target_version < (1, 1) and 'requests' in primitive:
            for index, request in enumerate(self.requests):
                request.obj_make_compatible(
                    primitive['requests'][index]['nova_object.data'], '1.0')
                primitive['requests'][index]['nova_object.version'] = '1.0'

    @classmethod
    def obj_from_db(cls, context, instance_uuid, db_requests):
        self = cls(context=context, requests=[],
                   instance_uuid=instance_uuid)
        if db_requests is not None:
            requests = jsonutils.loads(db_requests)
        else:
            requests = []
        for request in requests:
            request_obj = InstancePCIRequest(
                count=request['count'], spec=request['spec'],
                alias_name=request['alias_name'], is_new=request['is_new'],
                request_id=request['request_id'])
            request_obj.obj_reset_changes()
            self.requests.append(request_obj)
        self.obj_reset_changes()
        return self

    @base.remotable_classmethod
    def get_by_instance_uuid(cls, context, instance_uuid):
        db_pci_requests = db.instance_extra_get_by_instance_uuid(
                context, instance_uuid, columns=['pci_requests'])
        if db_pci_requests is not None:
            db_pci_requests = db_pci_requests['pci_requests']
        return cls.obj_from_db(context, instance_uuid, db_pci_requests)

    @classmethod
    def get_by_instance_uuid_and_newness(cls, context, instance_uuid, is_new):
        requests = cls.get_by_instance_uuid(context, instance_uuid)
        requests.requests = [x for x in requests.requests
                             if x.new == is_new]
        return requests

    @staticmethod
    def _load_legacy_requests(sysmeta_value, is_new=False):
        if sysmeta_value is None:
            return []
        requests = []
        db_requests = jsonutils.loads(sysmeta_value)
        for db_request in db_requests:
            request = InstancePCIRequest(
                count=db_request['count'], spec=db_request['spec'],
                alias_name=db_request['alias_name'], is_new=is_new)
            request.obj_reset_changes()
            requests.append(request)
        return requests

    @classmethod
    def get_by_instance(cls, context, instance):
        # NOTE (baoli): not all callers are passing instance as object yet.
        # Therefore, use the dict syntax in this routine
        if 'pci_requests' in instance['system_metadata']:
            # NOTE(danms): This instance hasn't been converted to use
            # instance_extra yet, so extract the data from sysmeta
            sysmeta = instance['system_metadata']
            _requests = (
                cls._load_legacy_requests(sysmeta['pci_requests']) +
                cls._load_legacy_requests(sysmeta.get('new_pci_requests'),
                                          is_new=True))
            requests = cls(instance_uuid=instance['uuid'], requests=_requests)
            requests.obj_reset_changes()
            return requests
        else:
            return cls.get_by_instance_uuid(context, instance['uuid'])

    def to_json(self):
        blob = [{'count': x.count,
                 'spec': x.spec,
                 'alias_name': x.alias_name,
                 'is_new': x.is_new,
                 'request_id': x.request_id} for x in self.requests]
        return jsonutils.dumps(blob)

    @base.remotable
    def save(self):
        blob = self.to_json()
        db.instance_extra_update_by_uuid(self._context, self.instance_uuid,
                                         {'pci_requests': blob})

    @classmethod
    def from_request_spec_instance_props(cls, pci_requests):
        objs = [InstancePCIRequest(**request)
            for request in pci_requests['requests']]
        return cls(requests=objs, instance_uuid=pci_requests['instance_uuid'])
