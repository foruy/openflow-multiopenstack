from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project import dashboard

class Users(horizon.Panel):
    name = _("Record List")
    slug = 'users'

dashboard.Project.register(Users)
