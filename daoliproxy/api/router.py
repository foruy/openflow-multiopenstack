import daoliproxy.api.openstack
from daoliproxy.api import extensions
from daoliproxy.api import firewalls
from daoliproxy.api import flavors
from daoliproxy.api import gateways
from daoliproxy.api import images
from daoliproxy.api import networks
from daoliproxy.api import resources
from daoliproxy.api import security_groups
from daoliproxy.api import servers
from daoliproxy.api import users
from daoliproxy.api import zones

class APIRouter(daoliproxy.api.openstack.APIRouter):
    """Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    ExtensionManager = extensions.ExtensionManager

    def _setup_routes(self, mapper, ext_mgr, init_only):
        mapper.redirect("", "/")

        user_controller = users.create_resource()
        mapper.connect("users", "/authenticate",
                       controller=user_controller,
                       action='authenticate',
                       conditions={"method": ['POST']})

        mapper.connect("users", "/authenticate/{user_id}",
                       controller=user_controller,
                       action='authenticate_by_zone',
                       conditions={"method": ['PUT']})

        mapper.connect("users", "/users",
                       controller=user_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("users", "/users/{id}",
                       controller=user_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("users", "/users/{id}",
                       controller=user_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("users", "/users/action",
                       controller=user_controller,
                       action='action',
                       conditions={"method": ['PUT']})

        mapper.connect("users", "/users/register",
                       controller=user_controller,
                       action='register',
                       conditions={"method": ['POST']})

        mapper.connect("users", "/user_login",
                       controller=user_controller,
                       action='login_list',
                       conditions={"method": ['GET']})

        mapper.connect("limits", "/limits",
                       controller=user_controller,
                       action='user_absolute_limits',
                       conditions={"method": ['GET']})

        mapper.connect("os-password", "/os-password",
                       controller=user_controller,
                       action='validate',
                       conditions={"method": ['PUT']})

        mapper.connect("os-password", "/os-password/userkey",
                       controller=user_controller,
                       action='update_key',
                       conditions={"method": ['PUT']})

        mapper.connect("os-password", "/os-password/getpassword",
                       controller=user_controller,
                       action='getpassword',
                       conditions={"method": ['PUT']})

        mapper.connect("os-password", "/os-password/resetpassword",
                       controller=user_controller,
                       action='resetpassword',
                       conditions={"method": ['PUT']})

        mapper.connect("os-proxy", "/os-proxy/authenticate/{user_id}",
                       controller=user_controller,
                       action='authenticate_by_zone_proxy',
                       conditions={"method": ['PUT']})

        mapper.connect("os-proxy", "/os-proxy/users/register",
                       controller=user_controller,
                       action='register_proxy',
                       conditions={"method": ['POST']})

        mapper.connect("os-proxy", "/os-proxy/os-password/resetpassword",
                       controller=user_controller,
                       action='resetpassword_proxy',
                       conditions={"method": ['PUT']})


        zone_controller = zones.create_resource()
        mapper.connect("zones", "/zones",
                       controller=zone_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("zones", "/zones/{id}",
                       controller=zone_controller,
                       action='get',
                       conditions={"method": ['GET']})


        mapper.connect("zones", "/zones",
                       controller=zone_controller,
                       action='rebuild',
                       conditions={"method": ['POST']})

        mapper.connect("zones", "/zones/{id}",
                       controller=zone_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("os-proxy", "/os-proxy/zones",
                       controller=zone_controller,
                       action='rebuild_proxy',
                       conditions={"method": ['POST']})

        server_controller = servers.create_resource()
        mapper.connect("servers", "/servers",
                       controller=server_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("servers", "/servers/detail",
                       controller=server_controller,
                       action='detail',
                       conditions={"method": ['GET']})

        mapper.connect("servers", "/servers/{id}",
                       controller=server_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("servers", "/servers",
                       controller=server_controller,
                       action='create',
                       conditions={"method": ['POST']})

        mapper.connect("servers", "/servers/{id}",
                       controller=server_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("servers", "/servers/{id}/action",
                       controller=server_controller,
                       action='action',
                       conditions={"method": ['POST']})

        mapper.connect("os-proxy", "/os-proxy/servers",
                       controller=server_controller,
                       action='create_proxy',
                       conditions={"method": ['POST']})

        mapper.connect("os-proxy", "/os-proxy/servers/{id}",
                       controller=server_controller,
                       action='delete_proxy',
                       conditions={"method": ['DELETE']})

        mapper.connect("os-proxy", "/os-proxy/servers/{id}/action",
                       controller=server_controller,
                       action='action',
                       conditions={"method": ['POST']})


        image_controller = images.create_resource()
        mapper.connect("images", "/images",
                       controller=image_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("images", "/images/{zone_id}",
                       controller=image_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("images", "/images/{image_id}",
                       controller=image_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("images", "/images",
                       controller=image_controller,
                       action='rebuild',
                       conditions={"method": ['PUT']})

        mapper.connect("os-proxy", "/os-proxy/images",
                       controller=image_controller,
                       action='rebuild_proxy',
                       conditions={"method": ['PUT']})

        flavor_controller = flavors.create_resource()
        mapper.connect("flavors", "/flavors",
                       controller=flavor_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("flavors", "/flavors/{zone_id}",
                       controller=flavor_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("flavors", "/flavors/{flavor_id}",
                       controller=flavor_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("flavors", "/flavors",
                       controller=flavor_controller,
                       action='rebuild',
                       conditions={"method": ['PUT']})

        mapper.connect("os-proxy", "/os-proxy/flavors",
                       controller=flavor_controller,
                       action='rebuild_proxy',
                       conditions={"method": ['PUT']})

        gateway_controller = gateways.create_resource()
        mapper.connect("gateways", "/gateways",
                       controller=gateway_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("gateways", "/gateways/{id}",
                       controller=gateway_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("gateways", "/gateways/{gateway_id}",
                       controller=gateway_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("gateways", "/gateways",
                       controller=gateway_controller,
                       action='rebuild',
                       conditions={"method": ['PUT']})

        mapper.connect("os-proxy", "/os-proxy/gateways",
                       controller=gateway_controller,
                       action='rebuild_proxy',
                       conditions={"method": ['PUT']})

        mapper.connect("gateways", "/os-gateways/instance/{instance_id}",
                       controller=gateway_controller,
                       action='get_by_instance',
                       conditions={"method": ['GET']})

        mapper.connect("gateways", "/os-gateways/zone/{zone_id}",
                       controller=gateway_controller,
                       action='get_by_zone',
                       conditions={"method": ['GET']})

        network_controller = networks.create_resource()
        mapper.connect("networks", "/networks",
                       controller=network_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("networks", "/networks/{zone_id}",
                       controller=network_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("networks", "/networks/{network_id}",
                       controller=network_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("networks", "/networks",
                       controller=network_controller,
                       action='rebuild',
                       conditions={"method": ['PUT']})

        mapper.connect("os-proxy", "/os-proxy/networks",
                       controller=network_controller,
                       action='rebuild_proxy',
                       conditions={"method": ['PUT']})

        mapper.connect("network-types", "/os-network",
                       controller=network_controller,
                       action='network_type_list',
                       conditions={"method": ['GET']})

        mapper.connect("network-types", "/os-network",
                       controller=network_controller,
                       action='network_type_delete',
                       conditions={"method": ['DELETE']})

        security_group_controller = security_groups.create_resource()
        mapper.connect("security_groups", "/security_groups",
                       controller=security_group_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("security_groups", "/security_groups",
                       controller=security_group_controller,
                       action='update',
                       conditions={"method": ['PUT']})

        firewall_controller = firewalls.create_resource()
        mapper.connect("firewalls", "/firewalls",
                       controller=firewall_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("firewalls", "/firewalls/{id}",
                       controller=firewall_controller,
                       action='get',
                       conditions={"method": ['GET']})

        mapper.connect("firewalls", "/firewalls/{id}",
                       controller=firewall_controller,
                       action='delete',
                       conditions={"method": ['DELETE']})

        mapper.connect("firewalls", "/firewalls",
                       controller=firewall_controller,
                       action='create',
                       conditions={"method": ['POST']})

        mapper.connect("firewalls", "/firewalls/{instance_id}/action",
                       controller=firewall_controller,
                       action='exists',
                       conditions={"method": ['POST']})

        resource_controller = resources.create_resource()
        mapper.connect("resources", "/resources",
                       controller=resource_controller,
                       action='list',
                       conditions={"method": ['GET']})

        mapper.connect("resources", "/resources/{user_id}",
                       controller=resource_controller,
                       action='get',
                       conditions={"method": ['GET']})
