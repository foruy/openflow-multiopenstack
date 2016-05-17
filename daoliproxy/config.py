# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
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

from oslo_config import cfg
from oslo_db import options
from oslo_log import log

from daoliproxy import debugger
from daoliproxy import paths
from daoliproxy import version


CONF = cfg.CONF

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('daoliproxy.sqlite')

_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                       'qpid=WARN', 'sqlalchemy=WARN', 'suds=INFO',
                       'oslo_messaging=INFO', 'iso8601=WARN',
                       'requests.packages.urllib3.connectionpool=WARN',
                       'urllib3.connectionpool=WARN', 'websocket=WARN',
                       'keystonemiddleware=WARN', 'routes.middleware=WARN',
                       'stevedore=WARN', 'glanceclient=WARN']

_DEFAULT_LOGGING_CONTEXT_FORMAT = ('%(asctime)s.%(msecs)03d %(process)d '
                                   '%(levelname)s %(name)s [%(request_id)s '
                                   '%(user_identity)s] %(instance)s'
                                   '%(message)s')


def parse_args(argv, default_config_files=None):
    log.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    log.register_options(CONF)
    options.set_defaults(CONF, connection=_DEFAULT_SQL_CONNECTION,
                         sqlite_db='daoliproxy.sqlite')
    debugger.register_cli_opts()
    CONF(argv[1:],
         project='daoliproxy',
         version=version.version_string(),
         default_config_files=default_config_files)
