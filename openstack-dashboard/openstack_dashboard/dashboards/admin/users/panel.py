from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.admin import dashboard

class Users(horizon.Panel):
    name = _("Users")
    slug = 'users'
    permissions = ('openstack.roles.admin',)

dashboard.Admin.register(Users)
