import logging

from django.conf import settings

from horizon import exceptions

__all__ = ('APIResourceWrapper', 'get_service_from_catalog', 'url_for',)

LOG = logging.getLogger(__name__)

class APIResourceWrapper(object):
    """Simple wrapper for api objects.

    Define _attrs on the child class and pass in the
    api object as the only argument to the constructor
    """
    _attrs = []
    _apiresource = None # Make sure _apiresource is there event in __init__.

    def __init__(self, apiresource):
        self._apiresource = apiresource

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._attrs:
                raise
            # __getattr__ won't find properties
            return getattr(self._apiresource, attr)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             dict((attr, getattr(self, attr))
                                  for attr in self._attrs
                                  if hasattr(self, attr)))


def get_service_from_catalog(catalog, service_type):
    if catalog:
        for service in catalog:
            if service['type'] == service_type:
                return service
    return None

def get_version_from_service(service):
    if service:
        endpoint = service['endpoints'][0]
        if 'interface' in endpoint:
            return 3
        else:
            return 2.0
    return 2.0

# Mapping of V2 Catalog Endpoint_type to V3 Catalog Interfaces
ENDPOINT_TYPE_TO_INTERFACE = {
    'publicURL': 'public',
    'internalURL': 'internal',
    'adminURL': 'admin',
}

def get_url_for_service(service, region, endpoint_type):
    identity_version = get_version_from_service(service)
    for endpoint in service['endpoints']:
        # ignore region for identity
        if service['type'] == 'identity' or region == endpoint['region']:
            try:
                if identity_version < 3:
                    return endpoint[endpoint_type]
                else:
                    interface = \
                        ENDPOINT_TYPE_TO_INTERFACE.get(endpoint_type, '')
                    if endpoint['interface'] == interface:
                        return endpoint['url']
            except (IndexError, KeyError):
                return None
    return None

def url_for(user, service_type, endpoint_type=None, region=None):
    endpoint_type = endpoint_type or getattr(settings,
                                             'OPENSTACK_ENDPOINT_TYPE',
                                             'publicURL')
    fallback_endpoint_type = getattr(settings, 'SECONDARY_ENDPOINT_TYPE', None)

    catalog = user.service_catalog
    service = get_service_from_catalog(catalog, service_type)
    if service:
        if not region:
            region = user.services_region
        url = get_url_for_service(service,
                                  region,
                                  endpoint_type)
        if not url and fallback_endpoint_type:
            url = get_url_for_service(service,
                                      region,
                                      fallback_endpoint_type)
        if url:
            return url
    raise exceptions.ServiceCatalogException(service_type)
