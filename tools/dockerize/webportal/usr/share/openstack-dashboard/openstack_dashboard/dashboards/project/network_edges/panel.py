from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project import dashboard

class NetworkEdge(horizon.Panel):
    name = _("Distributed Firewall")
    slug = 'network_edges'

dashboard.Project.register(NetworkEdge)
