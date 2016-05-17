from django.utils.translation import ugettext_lazy as _

import horizon


class Admin(horizon.Dashboard):
    name = _("Admin")
    slug = "admin"
    panels = ('instances', 'zones', 'users')
    default_panel = 'instances'
    permissions = ('openstack.roles.admin',)

horizon.register(Admin)
