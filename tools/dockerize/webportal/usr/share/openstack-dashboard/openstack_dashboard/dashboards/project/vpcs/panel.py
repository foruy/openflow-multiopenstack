from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.project import dashboard

class SecurityGroup(horizon.Panel):
    name = _("VPC")
    slug = 'vpcs'


dashboard.Project.register(SecurityGroup)
