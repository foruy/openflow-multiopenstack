"""
Views for managing vpcs.
"""
import json
import logging
import random
import traceback

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.utils.text import normalize_newlines
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect

from horizon import exceptions
from horizon.views import APIView

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances import utils as instance_utils
from openstack_dashboard.dashboards.project.images import utils as image_utils
from openstack_dashboard.utils import get_client_addr, get_client_type
#from proxyclient.openstack.common.apiclient.exceptions import  HTTPClientError

LOG = logging.getLogger(__name__)

WEBSERVICES = ["apache", "nginx", "php", "tomcat"]


class IndexView(APIView):
    template_name = 'project/vpcs/index.html'

    def get_data(self, request, context, *args, **kwargs):
        images = {}
        for image in get_images(request):
            if not images.has_key(image['type']):
                images[image['type']] = image
                images[image['type']]['image_id'] = "%s:%s" % (
                        image['id'], image['dc_id'])
            else:
                images[image['type']]['image_id'] += (" %s:%s" % (
                        image['id'], image['dc_id']))

        #context['images'] = images.values()
        context['vm_images'] = []
        context['container_images'] = []
        for image in images.values():
            if image["type"] == "vm":
                context["vm_images"].insert(0, image)
            else:
                context["container_images"].append(image)

        try:
            netypes = api.proxy.network_type_list(request)
        except:
            netypes = []
            exceptions.handle(request, _('Unable to retrieve network type.'),
                              ignore=True)

        context['netypes'] = netypes
        context['horizon_language'] = request.session.get(
                'horizon_language', request.LANGUAGE_CODE)
        return context

def get_images(request):
    _images = []
    _type = {"docker": "container", "container": "container"}
    for zone in get_zones(request):
        images = image_utils.get_available_images(request, zone.id)
        for image in images:
            _images.append({'id': image.imageid, 'name': image.name,
                           'type': image.display_format,
                           'category': _type.get(image.container_format, 'vm'),
                           'class': image.display_format,
                           'dc_id': zone.id,
                           'dc_name': zone.name})
    return _images


def get_zones(request, user=True):
    try:
        zones = api.proxy.availability_zone_list(request, user)
    except:
        zones = []
        exceptions.handle(request, _('Unable to retrieve zones.'), ignore=True)
    return zones

def _get_servers(request):
    servers = []

    image_dict = SortedDict([(img["id"], img)for img in get_images(request)])
    zone_dict = SortedDict([(zone.id, zone.name) for zone in get_zones(request)])
    gateway_dict = SortedDict([(g.hostname, g.vext_ip)
                              for g in api.proxy.gateway_list(request)])

    for server in api.proxy.server_list(request):
        image = image_dict.get(server.image_id, {})
        if zone_dict.has_key(server.zone_id):
            server.zone_id = zone_dict[server.zone_id]

        firewall = [(gateway_dict.get(f.hostname), f.gateway_port)
                    for f in api.proxy.firewall_get(request, server.id)]
        servers.append(server_format(request, server, image, firewall))

    return servers


def get_servers(request):
    ids = request.POST.getlist("ids")
    if not ids:
        ids = request.POST.getlist('ids[]')

    if not ids:
        return HttpResponse(json.dumps([]), content_type='application/json')

    try:
        data = []
        for d in _get_servers(request):

            if d.get("id", "") not in ids:
                continue
            data.append(d)
    except:
        LOG.error(traceback.format_exc())
        data = []

    return HttpResponse(json.dumps(data), content_type='application/json')

def server_format(request, server, image, firewall):
    type = {'docker': 'docker'}

    if not hasattr(server, 'addresses'):
        server.address = ""

    addresses = [addr['address'] for addr in server.addresses]

    data = {"id": server.id,
            "name": server.name,
            "pid": server.keystone_project_id,
            "ip": '|'.join(addresses),
            "gip": '',
            "port": '',
            "dc": server.zone_id,
            "status": server.status,
            "type": image.get("type", "UNKNOWN"),
            "category": image.get("category", "UNKNOWN"),
            "zone_name": image.get("dc_name", "UNKNOWN")}

    if firewall:
        data['gip'], data['port'] = firewall[0]
        if image.get("type") == "wordpress" and len(firewall) > 1:
            data["wordpress_port"] = firewall[1][1]
        else:
            data["wordpress_port"] = ""
        if image.get("type") in WEBSERVICES and len(firewall) > 1:
            data["webservice_port"] = firewall[1][1]
        else:
            data["webservice_port"] = ""

    return data

def show(request):
    _data = {"servers": [], "groups": {}}
    _data["servers"] = _get_servers(request)
    _data["groups"] = api.proxy.security_group_list(request).to_dict()

    response = HttpResponse(content_type='application/json')
    response.write(json.dumps(_data))
    response.flush()
    return response

def create(request):
    src, dst = validate(request.GET)
    kwargs = {'action': 'create', 'start': src['uid'], 'end': dst['uid']}
    api.proxy.security_group_update(request, **kwargs)
    return HttpResponse(status=204)

def delete(request):
    src, dst = validate(request.GET)
    kwargs = {'action': 'delete', 'start': src['uid'], 'end': dst['uid']}
    api.proxy.security_group_update(request, **kwargs)
    return HttpResponse(status=204)

def validate(post):
    src = {'uid': post.get('suid'),
           'pid': post.get('spid')}
    dst = {'uid': post.get('duid'),
           'pid': post.get('dpid')}
    if any([not src['uid'], not src['pid'], not dst['uid'], not dst['pid']]):
        raise exceptions.NotFound()
    src['uid'] = src['uid']
    dst['uid'] = dst['uid']
    return (src, dst)

def get_dcs(request):
    dcs = []
    for zone in get_zones(request, False):
        try:
            limit = api.proxy.project_absolute_limits(request, zone.id)
            if limit.maxTotalInstances - limit.totalInstancesUsed <= 0:
                disabled = True
            else:
                disabled = zone.disabled
        except:
            disabled = True

        _flavors = instance_utils.flavor_list(request, zone.id)
        flavors = instance_utils.sort_flavor_list(request, _flavors)

        dcs.append({"id": zone.id, "name": zone.name,
                    "disabled": disabled, "flavors": flavors})
    random.shuffle(dcs)

    return HttpResponse(json.dumps({"dcs": dcs}), content_type='application/json')

def _launch(request, zone_id):
    data = request.POST
    address = data.get('address', None)
    if address is not None:
        try:
            api.proxy.server_network(self.request, address)
        except:
            msg = _("This address was in used.")
            exceptions.handle(request, msg)
    try:
        instance = api.proxy.server_create(request,
                                           data['name'],
                                           data['image_id'],
                                           data['flavors'],
                                           zone_id=None,
                                           key_name=None,
                                           user_data=normalize_newlines(''),
                                           security_groups=None,
                                           block_device_mapping=None,
                                           block_device_mapping_v2=None,
                                           nics=None,
                                           availability_zone=None,
                                           instance_count=int(data.get('count', 1)),
                                           #instance_count=1,
                                           admin_pass=None,
                                           disk_config=None,
                                           accessIPv4=None,
                                           net_type=int(data['net_type']))
    except:
        LOG.error(traceback.format_exc())
        return HttpResponse(status=400)
    else:
        return HttpResponse(json.dumps(instance.servers), content_type='application/json')


def _launch_validate(data):
    try:
        if int(data['volume_size']) < 1:
            return 1

        if not data['volume_name']:
            return 2
    except Exception:
        return 3

    return 0


def launch(request, zone_id):
    data = request.POST

    dev_mapping_2 = []
    image_id = None
    if data.get('create_volume') == 'true':
        if _launch_validate(data):
            return HttpResponse(status=400)

        # The default is not backup
        volume_info = {'boot_index': '0',
                       'uuid': data['image_id'],
                       'volume_size': data['volume_size'],
                       'device_name': data['volume_name'],
                       'source_type': 'image',
                       'destination_type': 'volume',
                       'delete_on_termination': 0,
                       'is_backup': 1
                       }

        disk_info = {'instance_id':None,
                     'disk_name': data['volume_name'],
                     'disk_size': data['volume_size'],
                     'zonename':None,
                     'project_id':request.session["user_id"],
                     'status':'active'
                    }

        dev_mapping_2.append(volume_info)
    else:
        disk_info = None
        dev_mapping_2 = None
        image_id = data['image_id']

    request.session['netype'] = int(data['net_type'])

    try:
        instance = api.proxy.server_create(request,
                                           data['name'],
                                           image_id,
                                           data.get('flavors', 1),
                                           zone_id=zone_id,
                                           key_name=None,
                                           user_data=normalize_newlines(''),
                                           security_groups=None,
                                           block_device_mapping=None,
                                           block_device_mapping_v2=dev_mapping_2,
                                           nics=None,
                                           availability_zone=None,
                                           instance_count=int(data.get('count', 1)),
                                           #instance_count=1,
                                           admin_pass=None,
                                           disk_config=None,
                                           accessIPv4=None,
                                           net_type=int(data['net_type']))
        user_id = request.session["user_id"]
        instance_info = {'container_id':instance.servers[0]['id'],
                         'container_name':instance.servers[0]['name'],
                         'zonename':instance.servers[0]['zone_id'],
                         'flavor_id':instance.servers[0]['flavor_id']
                    }
        if disk_info:
            disk_info['instance_id'] = instance.servers[0]['id']
            disk_info['zonename'] = instance.servers[0]['zone_id']
    except:
        LOG.error(traceback.format_exc())
        return HttpResponse(status=400)
    else:
        return HttpResponse(json.dumps(instance.servers), content_type='application/json')


def stop(request, instance_id):
    try:
        api.proxy.server_stop(request, instance_id)
        status = 200
    except HTTPClientError as e:
        status = 423
    except Exception:
        LOG.error(traceback.format_exc())
        status = 400
    return HttpResponse(status=status)


def start(request, instance_id):
    try:
        api.proxy.server_start(request, instance_id)
        status = 200
    except HTTPClientError as e:
        status = 423
    except Exception:
        LOG.error(traceback.format_exc())
        status = 400

    return HttpResponse(status=status)


def terminate(request, instance_id):
    #try:
    #    # validate whether the password is correct
    #    username = request.user.username
    #    password = request.POST["password"]
    #    api.proxy.authenticate(request, username, password,
    #                           user_addr=get_client_addr(request),
    #                           user_type=get_client_type(request))
    #except Exception:
    #    #LOG.error(traceback.format_exc())
    #    return HttpResponse(status=403)

    try:
        api.proxy.server_delete(request, instance_id)
        status = 200
    except Exception:
        LOG.error(traceback.format_exc())
        status = 400

    return HttpResponse(status=status)

