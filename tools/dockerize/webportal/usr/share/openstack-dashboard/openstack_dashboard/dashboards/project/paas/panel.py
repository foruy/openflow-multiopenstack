from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Paas(horizon.Panel):
        name = _("Trusted PaaS Measurement")
        slug = 'paas'

dashboard.Project.register(Paas)
