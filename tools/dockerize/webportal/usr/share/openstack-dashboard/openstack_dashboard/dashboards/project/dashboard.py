from django.utils.translation import ugettext_lazy as _

import horizon

class Project(horizon.Dashboard):
    name = _("Tenant")
    slug = "project"
    panels = ('vpcs', 'network_edges', 'instances', 'monitors',
              'bill', 'users', 'whitepaper', 'hybrid', 'build',
              'storage', 'dbaas', 'migration', 'paas')
              
    default_panel = 'vpcs'

horizon.register(Project)
