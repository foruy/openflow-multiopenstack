from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project import dashboard

class Topology(horizon.Panel):
    name = _("Network Topology")
    slug = 'topology'

dashboard.Project.register(Topology)
