from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project import dashboard


class Bill(horizon.Panel):
    name = _("Billing")
    slug = 'bill'
#    permissions = ('openstack.roles.admin',)


dashboard.Project.register(Bill)

