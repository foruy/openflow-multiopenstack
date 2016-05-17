from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project import dashboard

class Monitors(horizon.Panel):
    name = _("Monitoring")
    slug = 'monitors'


dashboard.Project.register(Monitors)
