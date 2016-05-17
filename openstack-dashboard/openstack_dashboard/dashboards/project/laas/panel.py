from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Laas(horizon.Panel):
    name = _("LBaaS")
    slug = 'laas'

dashboard.Project.register(Laas)
