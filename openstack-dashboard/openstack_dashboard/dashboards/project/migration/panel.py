from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.project import dashboard

class Migration(horizon.Panel):
    name = _("Migration")
    slug = 'migration'

dashboard.Project.register(Migration)

