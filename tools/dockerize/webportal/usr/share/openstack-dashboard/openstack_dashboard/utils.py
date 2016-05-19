# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
from six.moves.urllib import parse as urlparse

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import middleware
from django.utils import timezone

from keystoneclient.v2_0 import client as client_v2
from keystoneclient.v3 import client as client_v3


"""
We need the request object to get the user, so we'll slightly modify the
existing django.contrib.auth.get_user method. To do so we update the
auth middleware to point to our overridden method.

Calling the "patch_middleware_get_user" method somewhere like our urls.py
file takes care of hooking it in appropriately.
"""


def middleware_get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = get_user(request)
    return request._cached_user


def get_user(request):
    try:
        user_id = request.session[auth.SESSION_KEY]
        backend_path = request.session[auth.BACKEND_SESSION_KEY]
        backend = auth.load_backend(backend_path)
        backend.request = request
        user = backend.get_user(user_id) or AnonymousUser()
    except KeyError:
        user = AnonymousUser()
    return user


def patch_middleware_get_user():
    middleware.get_user = middleware_get_user
    auth.get_user = get_user


""" End Monkey-Patching. """


def check_token_expiration(token):
    """ Timezone-aware checking of the auth token's expiration timestamp.

    Returns ``True`` if the token has not yet expired, otherwise ``False``.
    """
    expiration = token.expires
    if settings.USE_TZ and timezone.is_naive(expiration):
        # Presumes that the Keystone is using UTC.
        expiration = timezone.make_aware(expiration, timezone.utc)
    # In case we get an unparseable expiration timestamp, return False
    # so you can't have a "forever" token just by breaking the expires param.
    if expiration:
        return expiration > timezone.now()
    else:
        return False


# Copied from Keystone's keystone/common/cms.py file.
PKI_ANS1_PREFIX = 'MII'


def is_ans1_token(token):
    '''
    thx to ayoung for sorting this out.

    base64 decoded hex representation of MII is 3082
    In [3]: binascii.hexlify(base64.b64decode('MII='))
    Out[3]: '3082'

    re: http://www.itu.int/ITU-T/studygroups/com17/languages/X.690-0207.pdf

    pg4:  For tags from 0 to 30 the first octet is the identfier
    pg10: Hex 30 means sequence, followed by the length of that sequence.
    pg5:  Second octet is the length octet
          first bit indicates short or long form, next 7 bits encode the number
          of subsequent octets that make up the content length octets as an
          unsigned binary int

          82 = 10000010 (first bit indicates long form)
          0000010 = 2 octets of content length
          so read the next 2 octets to get the length of the content.

    In the case of a very large content length there could be a requirement to
    have more than 2 octets to designate the content length, therefore
    requiring us to check for MIM, MIQ, etc.
    In [4]: base64.b64encode(binascii.a2b_hex('3083'))
    Out[4]: 'MIM='
    In [5]: base64.b64encode(binascii.a2b_hex('3084'))
    Out[5]: 'MIQ='
    Checking for MI would become invalid at 16 octets of content length
    10010000 = 90
    In [6]: base64.b64encode(binascii.a2b_hex('3090'))
    Out[6]: 'MJA='
    Checking for just M is insufficient

    But we will only check for MII:
    Max length of the content using 2 octets is 7FFF or 32767
    It's not practical to support a token of this length or greater in http
    therefore, we will check for MII only and ignore the case of larger tokens
    '''
    return token[:3] == PKI_ANS1_PREFIX


# From django.contrib.auth.views
# Added in Django 1.4.3, 1.5b2
# Vendored here for compatibility with old Django versions.
def is_safe_url(url, host=None):
    """
    Return ``True`` if the url is a safe redirection (i.e. it doesn't point to
    a different host).

    Always returns ``False`` on an empty url.
    """
    if not url:
        return False
    netloc = urlparse.urlparse(url)[1]
    return not netloc or netloc == host


# Helper for figuring out keystone version
# Implementation will change when API version discovery is available
def get_keystone_version():
    return getattr(settings, 'OPENSTACK_API_VERSIONS', {}).get('identity', 2.0)


def get_keystone_client():
    if get_keystone_version() < 3:
        return client_v2
    else:
        return client_v3

def get_client_addr(request):
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        client_addr = request.META['HTTP_X_FORWARDED_FOR']
    else:
        client_addr = request.META.get('REMOTE_ADDR', '')
    return client_addr

def get_client_type(request):
    format = "%s (%s)"
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    try:
        if (user_agent.find("MSIE") != -1):
            ie = user_agent.split('; ')
            client_type = format % tuple(ie[1:3])
        elif (user_agent.find("Chrome") != -1):
            chrome = [user_agent.split()[-1]]
            chrome.append(re.split('[()]', user_agent)[1])
            client_type = format % tuple(chrome)
        elif (user_agent.find("Firefox") != -1):
            firefox = [user_agent.split()[-1]]
            firefox.append(re.split('[()]', user_agent)[1])
            client_type = format % tuple(firefox)
        else:
            client_type = user_agent
    except:
        client_type = "Unknown"
    return client_type
