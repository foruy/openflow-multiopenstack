from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Dbaas(horizon.Panel):
    name = _("DBaaS")
    slug = 'dbaas'

dashboard.Project.register(Dbaas)
