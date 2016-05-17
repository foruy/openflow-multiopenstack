from oslo_config import cfg

from proxyclient.v2 import client as proxy_client

CONF = cfg.CONF

def proxyclient(request):
    conn = proxy_client.Client(request.user_name,
                               request.auth_token,
                               user_id=request.user_id,
                               project_id=request.project_id,
                               auth_url=request.auth_url,
                               insecure=False,
                               cacert=None,
                               http_log_debug=CONF.debug)
    conn.client.auth_token = request.auth_token
    conn.client.management_url = request.auth_url
    return conn

# User
def authenticate_by_zone_proxy(request, user_id, zone_id):
    return proxyclient(request).proxy.authenticate_by_zone(user_id, zone_id)

def register_proxy(request, user_id, zone_id):
    return proxyclient(request).proxy.register(user_id, zone_id)

def resetpassword_proxy(request, zone_id=None, username=None, password=None):
    return proxyclient(request).proxy.resetpassword(
            zone_id=zone_id, username=username, password=password)

# Flavor
def flavor_rebuild_proxy(request, body):
    return proxyclient(request).proxy.flavor_rebuild(body)

# Network
def network_rebuild_proxy(request, body):
    return proxyclient(request).proxy.network_rebuild(body)

# Gateway
def gateway_rebuild_proxy(request, body):
    return proxyclient(request).proxy.gateway_rebuild(body)

# Image
def image_rebuild_proxy(request, body):
    return proxyclient(request).proxy.image_rebuild(body)

# Zone
def zone_create_proxy(request, body):
    return proxyclient(request).proxy.zone_create(body)

# Server
def server_create_proxy(request, base, server, kwargs):
    return proxyclient(request).proxy.server_create(base, server, kwargs)

def server_delete_proxy(request, id):
    proxyclient(request).proxy.server_delete(id)

def server_start_proxy(request, id):
    proxyclient(request).proxy.server_start(id)

def server_stop_proxy(request, id):
    proxyclient(request).proxy.server_stop(id)
