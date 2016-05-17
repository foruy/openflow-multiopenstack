from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.zones \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.zones \
    import tabs as admin_tabs
from openstack_dashboard.dashboards.admin.zones \
    import forms as admin_forms

class AdminIndexView(tables.DataTableView):
    table_class = admin_tables.AdminZonesTable
    template_name = 'admin/zones/index.html'

    def get_data(self):
        try:
            zones = api.proxy.availability_zone_list(self.request, True)
        except Exception:
            zones = []
            exceptions.handle(self.request,
                              _('Unable to retrieve zone list.'),
                              ignore=True)
        return zones

class AdminDetailView(tabs.TabbedTableView):
    tab_group_class = admin_tabs.DetailTabs
    template_name = 'admin/zones/detail.html'

class AdminCreateView(forms.ModalFormView):
    form_class = admin_forms.ZoneForm
    template_name = 'admin/zones/create.html'
    success_url = reverse_lazy('horizon:admin:zones:index')
