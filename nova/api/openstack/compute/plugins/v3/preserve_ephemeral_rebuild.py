# Copyright 2015 IBM Corp.
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


from oslo_utils import strutils

from nova.api.openstack.compute.schemas.v3 import preserve_ephemeral_rebuild
from nova.api.openstack import extensions

ALIAS = "os-preserve-ephemeral-rebuild"


class PreserveEphemeralRebuild(extensions.V3APIExtensionBase):
    """Allow preservation of the ephemeral partition on rebuild."""

    name = "PreserveEphemeralOnRebuild"
    alias = ALIAS
    version = 1

    def get_controller_extensions(self):
        return []

    def get_resources(self):
        return []

    def server_rebuild(self, rebuild_dict, rebuild_kwargs,
                      body_deprecated_param=None):
        if 'preserve_ephemeral' in rebuild_dict:
            rebuild_kwargs['preserve_ephemeral'] = strutils.bool_from_string(
                rebuild_dict['preserve_ephemeral'], strict=True)

    def get_server_rebuild_schema(self):
        return preserve_ephemeral_rebuild.server_rebuild
