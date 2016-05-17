from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Hybrid(horizon.Panel):
    name = _("Hybrid Cloud")
    slug = 'hybrid'

dashboard.Project.register(Hybrid)
