"""Utilities and helper functions."""

import inspect
import os
import sys
import pyclbr
import random
import six.moves.urllib.parse as urlparse

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from daoliproxy.i18n import _, _LE, _LW

monkey_patch_opts = [
    cfg.BoolOpt('monkey_patch',
                default=False,
                help='Whether to log monkey patching'),
    cfg.ListOpt('monkey_patch_modules',
                default=[],
                help='List of modules/decorators to monkey patch'),
]

utils_opts = [
    cfg.IntOpt('password_length',
               default=8,
               help='Length of generated user passwords'),
]

CONF = cfg.CONF
CONF.register_opts(monkey_patch_opts)
CONF.register_opts(utils_opts)

LOG = logging.getLogger(__name__)

USER_FILTERS = [
    'admin', 'root', 'demo', 'service', 'services', 'horizon', 'dashboard',
    'nova', 'keystone', 'cinder', 'glance', 'swift', 'ceilometer', 'heat',
]

def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = _get_root_helper()
    return processutils.execute(*cmd, **kwargs)

def daoliproxydir():
    import daoliproxy
    return os.path.abspath(daoliproxy.__file__).split('daoliproxy/__init__.py')[0]


def generate_uid(topic, size=8):
    characters = '01234567890abcdefghijklmnopqrstuvwxyz'
    choices = [random.choice(characters) for _x in xrange(size)]
    return '%s-%s' % (topic, ''.join(choices))

def utf8(value):
    """Try to turn a string into utf-8 if possible.

    Code is directly from the utf8 function in
    http://github.com/facebook/tornado/blob/master/tornado/escape.py

    """
    if isinstance(value, unicode):
        return value.encode('utf-8')
    assert isinstance(value, str)
    return value

# Default symbols to use for passwords. Avoids visually confusing characters.
# ~6 bits per symbol
DEFAULT_PASSWORD_SYMBOLS = ('23456789',  # Removed: 0,1
                            'ABCDEFGHJKLMNPQRSTUVWXYZ',   # Removed: I, O
                            'abcdefghijkmnopqrstuvwxyz')  # Removed: l

def generate_password(length=None, symbolgroups=DEFAULT_PASSWORD_SYMBOLS):
    """Generate a random password from the supplied symbol groups.

    At least one symbol from each group will be included. Unpredictable
    results if length is less than the number of symbol groups.

    Believed to be reasonably secure (with a reasonable password length!)

    """
    if length is None:
        length = CONF.password_length

    r = random.SystemRandom()

    password = [r.choice(s) for s in symbolgroups]
    r.shuffle(password)
    password = password[:length]
    length -= len(password)

    symbols = ''.join(symbolgroups)
    password.extend([r.choice(symbols) for _i in xrange(length)])

    r.shuffle(password)

    return ''.join(password)

def monkey_patch():
    """If the CONF.monkey_patch set as True,
    this function patches a decorator
    for all functions in specified modules.
    You can set decorators for each modules
    using CONF.monkey_patch_modules.
    The format is "Module path:Decorator function".
    Example:
    'nova.api.ec2.cloud:nova.notifications.notify_decorator'

    Parameters of the decorator is as follows.
    (See nova.notifications.notify_decorator)

    name - name of the function
    function - object of the function
    """
    # If CONF.monkey_patch is not True, this function do nothing.
    if not CONF.monkey_patch:
        return
    # Get list of modules and decorators
    for module_and_decorator in CONF.monkey_patch_modules:
        module, decorator_name = module_and_decorator.split(':')
        # import decorator function
        decorator = importutils.import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key in module_data.keys():
            # set the decorator for the class methods
            if isinstance(module_data[key], pyclbr.Class):
                clz = importutils.import_class("%s.%s" % (module, key))
                for method, func in inspect.getmembers(clz, inspect.ismethod):
                    setattr(clz, method,
                        decorator("%s.%s.%s" % (module, key, method), func))
            # set the decorator for the function
            if isinstance(module_data[key], pyclbr.Function):
                func = importutils.import_class("%s.%s" % (module, key))
                setattr(sys.modules[module], key,
                    decorator("%s.%s" % (module, key), func))

def replace_url(url, host=None, port=None, path=None):
    o = urlparse.urlparse(url)
    _host = o.hostname
    _port = o.port
    _path = o.path

    if host is not None:
        _host = host

    if port is not None:
        _port = port

    netloc = _host

    if _port is not None:
        netloc = ':'.join([netloc, str(_port)])

    if path is not None:
        _path = path

    return '%s://%s%s' % (o.scheme, netloc, _path)
