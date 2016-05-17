from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.admin import dashboard

class Zones(horizon.Panel):
    name = _("Zones")
    slug = 'zones'
    permissions = ('openstack.roles.admin',)

dashboard.Admin.register(Zones)
