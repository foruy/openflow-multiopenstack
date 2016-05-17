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

"""
Websocket proxy that is compatible with OpenStack Nova
SPICE HTML5 consoles. Leverages websockify.py by Joel Martin
"""

import sys

from oslo_config import cfg

from nova.cmd import baseproxy
from nova import config


opts = [
    cfg.StrOpt('html5proxy_host',
               default='0.0.0.0',
               help='Host on which to listen for incoming requests'),
    cfg.IntOpt('html5proxy_port',
               default=6082,
               help='Port on which to listen for incoming requests'),
    ]

CONF = cfg.CONF
CONF.register_cli_opts(opts, group='spice')


def main():
    config.parse_args(sys.argv)

    baseproxy.proxy(
        host=CONF.spice.html5proxy_host,
        port=CONF.spice.html5proxy_port)
