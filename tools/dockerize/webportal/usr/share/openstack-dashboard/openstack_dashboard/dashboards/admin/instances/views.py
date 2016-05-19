from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.instances \
    import tables as project_tables

class AdminIndexView(tables.DataTableView):
    table_class = project_tables.AdminInstancesTable
    template_name = 'admin/instances/index.html'

    def get_data(self):
        instances = []
        try:
            instances = api.proxy.server_list(self.request, all_tenants=True)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))

        if instances:
            try:
                users = api.proxy.user_list(self.request)
            except Exception:
                users = []
                msg = _('Unable to retrieve instance project information.')
                exceptions.handle(self.request, msg)

            user_dict = SortedDict([(u.id, u.username) for u in users])

            for inst in instances:
                inst.user_name = user_dict.get(inst.user_id, None)

        return instances
