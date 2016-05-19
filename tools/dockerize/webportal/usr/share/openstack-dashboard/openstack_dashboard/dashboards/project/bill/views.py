import json
import logging

from django.http import HttpResponse

from horizon.views import APIView
from  horizon import exceptions

from openstack_dashboard.api import bill

LOG = logging.getLogger(__name__)


class IndexView(APIView):
    template_name = 'project/bill/index.html'

    def get_data(self, request, context, *args, **kwargs):
        #LOG.info("-------------------------------------\n{0}".format(bill.get_all(request.user.tenant_id)))
        return context


def get_all(request):
    data = {
        "total_cost": "111.10",
        "balance": "50.10",
        "info": {
            "containers": [
                {
                    "id": "ID1",
                    "name": "name1",
                    "runtime": 111,
                    "cost": "11.1",
                    "zone": "shanghai",
                    "status": "active",
                    "price": 0.45,
                },
                {
                    "id": "ID2",
                    "name": "name2",
                    "runtime": 222,
                    "cost": "22.2",
                    "zone": "shanghai",
                    "status": "deleted",
                    "price": 0.45,
                },
                {
                    "id": "ID3",
                    "name": "name3",
                    "runtime": 333,
                    "cost": "33.3",
                    "zone": "beijing",
                    "status": "active",
                    "price": 0.45,
                },
            ],
            "disks": [
            ]
        }
    }
    #return HttpResponse(json.dumps(data), content_type='application/json')

    #_request = request.user.user_dict[context['project_id']]
    project_id = request.session["user_id"] 
    #project_id = bill.get_user_id_by_projectid(project_id) 
    LOG.info("==================user_id:{0}====\n".format(project_id))
    data = bill.get_all(project_id)
    return HttpResponse(json.dumps(data), content_type='application/json')
