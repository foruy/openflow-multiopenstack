from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Build(horizon.Panel):
    name = _("Build, Ship & Run")
    slug = 'build'

dashboard.Project.register(Build)
