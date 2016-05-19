from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Storage(horizon.Panel):
    name = _("Protected Storage")
    slug = 'storage'

dashboard.Project.register(Storage)
