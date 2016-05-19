# encoding: utf-8
from __future__ import absolute_import
import logging

#import bill

from bill import api

LOG = logging.getLogger(__name__)


def get_all(project_id):
    result = {"info": {}}

    data = api.get_balance_and_total_cost(project_id)
    if not data:
        return None
    else:
        #result["total_cost"] = data['total_cost']
        #result['balance'] = data['balance']
        result.update(data)
    container_data = api.get_containers_cost_details(project_id)
    disk_data = api.get_disks_cost_details(project_id)
    #LOG.info("============container_data:{0}====\n".format(container_data))
    #LOG.info("===========disk_data:{0}===\n".format(disk_data))
    if not container_data or not disk_data:
        return None
    #if 'container_cost_details' in container_data:
    result["info"]['containers'] = container_data.get("container_cost_details", [])
    #if 'disk_cost_details' in disk_data:
    result['info']['disks'] = disk_data.get('disk_cost_details', [])
    #result['info']['nass'] = []
    #result['info']['lBas'] = []
    #result['info']['dBaas'] = []
    #result['info']['publicIP'] = []
    #result['info']['vm'] = []
    #result['info']['network'] = []
    #LOG.info("==========result:{0}====\n".format(result))
    #result['info']['other'] = []
    #else:
    #    retult['info']['disks'] = []
        #result["info"]['disks'] = [
        #          {
        #            "id": "1111111111",
        #            "name": "disk1",
        #            "size": 222,
        #            "cost": "22.2",
        #            "zone": "shanghai",
        #            "status": "deleted",
        #            "price": 0.32,
        #        },
        #        {
        #            "id": "222222222",
        #            "name": "disk2",
        #            "size": 333,
        #            "cost": "33.3",
        #            "zone": "beijing",
        #            "status": "active",
        #            "price": 0.45,
        #        },
        #          ]

    return result


def get_user_id_by_projectid(project_id):
    return api.get_user_by_project(project_id)
