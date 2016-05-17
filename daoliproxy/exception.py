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

"""Proxy base exception handling.

Includes decorator for re-raising Proxy-type exceptions.

SHOULD include dedicated exception logging.

"""

import functools
import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
import webob.exc

from daoliproxy.i18n import _, _LE
from daoliproxy import safe_utils

from keystoneclient import exceptions as keystoneclient
from novaclient import exceptions as novaclient

LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='Make exception message format errors fatal'),
]

CONF = cfg.CONF
CONF.register_opts(exc_log_opts)


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


def _cleanse_dict(original):
    """Strip all admin_password, new_pass, rescue_pass keys from a dict."""
    return {k: v for k, v in original.iteritems() if "_pass" not in k}


def wrap_exception(notifier=None, get_notifier=None):
    """This decorator wraps a method to catch any exceptions that may
    get thrown. It also optionally sends the exception to the notification
    system.
    """
    def inner(f):
        def wrapped(self, context, *args, **kw):
            # Don't store self or context in the payload, it now seems to
            # contain confidential information.
            try:
                return f(self, context, *args, **kw)
            except Exception as e:
                with excutils.save_and_reraise_exception():
                    if notifier or get_notifier:
                        payload = dict(exception=e)
                        call_dict = safe_utils.getcallargs(f, context,
                                                           *args, **kw)
                        cleansed = _cleanse_dict(call_dict)
                        payload.update({'args': cleansed})

                        # If f has multiple decorators, they must use
                        # functools.wraps to ensure the name is
                        # propagated.
                        event_type = f.__name__

                        (notifier or get_notifier()).error(context,
                                                           event_type,
                                                           payload)

        return functools.wraps(f)(wrapped)
    return inner


class ProxyException(Exception):
    """Base Proxy Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_LE('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))    # noqa

                if CONF.fatal_exception_format_errors:
                    raise exc_info[0], exc_info[1], exc_info[2]
                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(ProxyException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full ProxyException message, (see __init__)
        return self.args[0]


class Invalid(ProxyException):
    msg_fmt = _("Unacceptable parameters.")
    code = 400

class MalformedRequestBody(ProxyException):
    msg_fmt = _("Malformed message body: %(reason)s")

# NOTE(johannes): NotFound should only be used when a 404 error is
# appropriate to be returned
class ConfigNotFound(ProxyException):
    msg_fmt = _("Could not find config at %(path)s")

class PasteAppNotFound(ProxyException):
    msg_fmt = _("Could not load paste app '%(name)s' from %(path)s")


class NotFound(ProxyException):
    msg_fmt = _("Resource could not be found.")
    code = 404

class InstanceNotFound(NotFound):
    msg_fmt = _("Instance %(instance)s could not be found.")

class UserNotFound(NotFound): #p
    msg_fmt = _("User %(user)s could not be found.")

class ZoneNotFound(NotFound): #p
    msg_fmt = _("Zone %(zone)s could not be found.")

class TokenNotFound(NotFound): #p
    msg_fmt = _("Token %(token)s could not be found.")

class ServiceNotFound(NotFound): #p
    msg_fmt = _("Service %(service)s could not be found.")

class NetworkTypeNotFound(NotFound): #p
    msg_fmt = _("Network type %(id)s could not be found.")


class Forbidden(ProxyException):
    ec2_code = 'AuthFailure'
    msg_fmt = _("Not authorized.")
    code = 403


class AdminRequired(Forbidden):
    msg_fmt = _("User does not have admin privileges")


class PolicyNotAuthorized(Forbidden):
    msg_fmt = _("Policy doesn't allow %(action)s to be performed.")


class Invalid(ProxyException):
    msg_fmt = _("Unacceptable parameters.")
    code = 400

class ValidationError(Invalid):
    msg_fmt = "%(detail)s"

class InvalidContentType(Invalid):
    msg_fmt = _("Invalid content type %(content_type)s.")

class InvalidAPIVersionString(Invalid):
    msg_fmt = _("API Version String %(version)s is of invalid format. Must "
                "be of format MajorNum.MinorNum.")

class VersionNotFoundForAPIMethod(Invalid):
    msg_fmt = _("API version %(version)s is not supported on this method.")


class InvalidGlobalAPIVersion(Invalid):
    msg_fmt = _("Version %(req_ver)s is not supported by the API. Minimum "
                "is %(min_ver)s and maximum is %(max_ver)s.")

class Forbidden(ProxyException):
    msg_fmt = _("Not authorized.")
    code = 403

class AdminRequired(Forbidden):
    msg_fmt = _("User %(user)s does not have admin privileges")
