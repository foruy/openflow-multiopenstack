from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.admin import dashboard

class Gateways(horizon.Panel):
    name = _("Gateways")
    slug = 'gateways'
    permissions = ('openstack.roles.admin',)

dashboard.Admin.register(Gateways)
