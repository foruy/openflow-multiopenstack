from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.admin import dashboard

class Instances(horizon.Panel):
    name = _("Instances")
    slug = 'instances'
    permissions = ('openstack.roles.admin',)

dashboard.Admin.register(Instances)
