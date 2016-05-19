import logging
import os
import sys
import warnings

import django
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import exceptions
from openstack_dashboard.static_settings import get_staticfiles_dirs  # noqa


warnings.formatwarning = lambda message, category, *args, **kwargs: \
    '%s: %s' % (category.__name__, message)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = '/usr/bin'

if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SITE_BRANDING = 'OpenStack Dashboard'

WEBROOT = '/dashboard/'
REDIRECT_URL = WEBROOT
LOGIN_URL = WEBROOT + 'login/'
LOGOUT_URL = WEBROOT + 'logout/'
LOGIN_REDIRECT_URL = WEBROOT + 'index/'

TIME_ZONE = "UTC"

ROOT_URLCONF = 'openstack_dashboard.urls'

HORIZON_CONFIG = {
    'dashboards': ('project', 'admin', 'settings',),
    'default_dashboard': 'project',
    'user_home': 'openstack_dashboard.views.get_user_home',
    'ajax_queue_limit': 10,
    'auto_fade_alerts': {
        'delay': 3000,
        'fade_duration': 1500,
        'types': ['alert-success', 'alert-info']
    },
    'help_url': "http://docs.openstack.org",
    'exceptions': {'recoverable': exceptions.RECOVERABLE,
                   'not_found': exceptions.NOT_FOUND,
                   'unauthorized': exceptions.UNAUTHORIZED},
    'angular_modules': [],
    'js_files': [],
    'js_spec_files': [],
}

#SUBNETWORK = [(1, '192.168.0.0/16'), (2, '172.16.0.0/12'), (3, '10.0.0.0/8'),]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'openstack_dashboard.middleware.HorizonMiddleware',
)
if django.VERSION >= (1, 8, 0):
    MIDDLEWARE_CLASSES += (
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',)
else:
    MIDDLEWARE_CLASSES += ('django.middleware.doc.XViewMiddleware',)
MIDDLEWARE_CLASSES += (
    #'horizon.middleware.HorizonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'horizon.context_processors.horizon',
    #'openstack_dashboard.context_processors.openstack',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'horizon.loaders.TemplateLoader',
)

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lesscpy {infile}'),
    ('text/scss', 'django_pyscss.compressor.DjangoScssFilter'),
)

COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
)

COMPRESS_ENABLED = True
COMPRESS_OUTPUT_DIR = 'dashboard'
COMPRESS_CSS_HASHING_METHOD = 'hash'
COMPRESS_PARSER = 'compressor.parser.HtmlParser'
COMPRESS_OFFLINE = True

INSTALLED_APPS = [
    'openstack_dashboard',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_pyscss',
    'openstack_dashboard.django_pyscss_fix',
    'compressor',
    'horizon',
]

MANAGEMENT_URL = 'http://127.0.0.1:65534'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
AUTHENTICATION_BACKENDS = ('openstack_dashboard.backend.KeystoneBackend',)
AUTHENTICATION_URLS = ['openstack_auth.urls']
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False
SESSION_TIMEOUT = 1800
# A token can be near the end of validity when a page starts loading, and
# invalid during the rendering which can cause errors when a page load.
# TOKEN_TIMEOUT_MARGIN defines a time in seconds we retrieve from token
# validity to avoid this issue. You can adjust this time depending on the
# performance of the infrastructure.
TOKEN_TIMEOUT_MARGIN = 10

# When using cookie-based sessions, log error when the session cookie exceeds
# the following size (common browsers drop cookies above a certain size):
SESSION_COOKIE_MAX_SIZE = 4093

# when doing upgrades, it may be wise to stick to PickleSerializer
# NOTE(berendt): Check during the K-cycle if this variable can be removed.
#                https://bugs.launchpad.net/horizon/+bug/1349463
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

LANGUAGES = (
    ('de', 'German'),
    ('en', 'English'),
    ('en-au', 'Australian English'),
    ('en-gb', 'British English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('ja', 'Japanese'),
    ('ko', 'Korean (Korea)'),
    ('pl', 'Polish'),
    ('pt-br', 'Portuguese (Brazil)'),
    ('ru', 'Russian'),
    ('zh-cn', 'Simplified Chinese'),
    ('zh-tw', 'Chinese (Taiwan)'),
)
LANGUAGE_CODE = 'en'
LANGUAGE_COOKIE_NAME = 'horizon_language'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_EXCEPTION_REPORTER_FILTER = 'horizon.exceptions.HorizonReporterFilter'

#POLICY_FILES_PATH = os.path.join(ROOT_PATH, "conf")
# Map of local copy of service policy files
#POLICY_FILES = {
#    'identity': 'keystone_policy.json',
#    'compute': 'nova_policy.json',
#    'volume': 'cinder_policy.json',
#    'image': 'glance_policy.json',
#    'orchestration': 'heat_policy.json',
#    'network': 'neutron_policy.json',
#    'telemetry': 'ceilometer_policy.json',
#}

ALLOWED_HOSTS = ['*']

ADD_INSTALLED_APPS = []

# STATIC directory for custom theme, set as default.
# It can be overridden in local_settings.py
CUSTOM_THEME_PATH = 'static/themes/default'

LOCAL_PATH = '/tmp'
SECRET_KEY='cffd90d9c2afb4c4bd1e'

if not WEBROOT.endswith('/'):
    WEBROOT += '/'
if LOGIN_URL is None:
    LOGIN_URL = WEBROOT + 'login/'
if LOGOUT_URL is None:
    LOGOUT_URL = WEBROOT + 'logout/'
if LOGIN_REDIRECT_URL is None:
    LOGIN_REDIRECT_URL = WEBROOT

MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))
#MEDIA_URL = WEBROOT + 'media/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))
#STATIC_URL = WEBROOT + 'static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = get_staticfiles_dirs(WEBROOT)

CUSTOM_THEME = os.path.join(ROOT_PATH, CUSTOM_THEME_PATH)
STATICFILES_DIRS.append(
    ('custom', CUSTOM_THEME),
)

# Load the pluggable dashboard settings
import openstack_dashboard.enabled
from openstack_dashboard import utils_settings

INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
utils_settings.update_dashboards(
    [
        openstack_dashboard.enabled,
    ],
    HORIZON_CONFIG,
    INSTALLED_APPS,
)
INSTALLED_APPS[0:0] = ADD_INSTALLED_APPS

# Ensure that we always have a SECRET_KEY set, even when no local_settings.py
# file is present. See local_settings.py.example for full documentation on the
# horizon.utils.secret_key module and its use.
if not SECRET_KEY:
    if not LOCAL_PATH:
        LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'local')

    from horizon.utils import secret_key
    SECRET_KEY = secret_key.generate_or_read_from_file(os.path.join(LOCAL_PATH,
                                                       '.secret_key_store'))

# Add HORIZON_CONFIG to the context information for offline compression
COMPRESS_OFFLINE_CONTEXT = {
    'STATIC_URL': STATIC_URL,
    'HORIZON_CONFIG': HORIZON_CONFIG,
}

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)

# during django reloads and an active user is logged in, the monkey
# patch below will not otherwise be applied in time - resulting in developers
# appearing to be logged out.  In typical production deployments this section
# below may be omitted, though it should not be harmful
from openstack_dashboard import utils as auth_utils
auth_utils.patch_middleware_get_user()

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

LOGGING = {
    'version': 1,
    # When set to True this will disable all logging except
    # for loggers specified in this configuration dictionary. Note that
    # if nothing is specified here and disable_existing_loggers is True,
    # django.db.backends will still log unless it is disabled explicitly.
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            # Set the level to "DEBUG" for verbose output logging.
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # Logging from django.db.backends is VERY verbose, send to null
        # by default.
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
        },
        'requests': {
            'handlers': ['null'],
            'propagate': False,
        },
        'horizon': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'openstack_dashboard': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'proxyclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'novaclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cinderclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'keystoneclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'glanceclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'neutronclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'heatclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ceilometerclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'troveclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'swiftclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'openstack_auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'nose.plugins.manager': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'iso8601': {
            'handlers': ['null'],
            'propagate': False,
        },
        'scss': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}
