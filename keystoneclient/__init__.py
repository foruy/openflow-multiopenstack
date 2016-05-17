# Copyright 2012 OpenStack Foundation
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

"""The python bindings for the OpenStack Identity (Keystone) project.

A Client object will allow you to communicate with the Identity server. The
recommended way to get a Client object is to use
:py:func:`keystoneclient.client.Client()`. :py:func:`~.Client()` uses version
discovery to create a V3 or V2 client depending on what versions the Identity
server supports and what version is requested.

Identity V2 and V3 clients can also be created directly. See
:py:class:`keystoneclient.v3.client.Client` for the V3 client and
:py:class:`keystoneclient.v2_0.client.Client` for the V2 client.

"""


import pbr.version

from keystoneclient import access
from keystoneclient import client
from keystoneclient import exceptions
from keystoneclient import generic
from keystoneclient import httpclient
from keystoneclient import service_catalog
from keystoneclient import v2_0
from keystoneclient import v3


#__version__ = pbr.version.VersionInfo('python-keystoneclient').version_string()
__version__ = '1.3.0'

__all__ = [
    # Modules
    'generic',
    'v2_0',
    'v3',

    # Packages
    'access',
    'client',
    'exceptions',
    'httpclient',
    'service_catalog',
]
