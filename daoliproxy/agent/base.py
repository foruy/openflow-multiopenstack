from daoliproxy import exception

    
def url_for(catalog, service_type, endpoint_type='publicURL'):
    if catalog.has_key(service_type):
        return catalog[service_type][endpoint_type]

    raise exception.ServiceNotFound(service=service_type)
