from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.users \
    import forms as admin_forms
from openstack_dashboard.dashboards.admin.users \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.users \
    import tabs as admin_tabs

class AdminIndexView(tables.DataTableView):
    table_class = admin_tables.AdminUsersTable
    template_name = 'admin/users/index.html'

    def get_data(self):
        try:
            users = api.proxy.user_list(self.request)
        except Exception:
            users = []
            exceptions.handle(self.request,
                              _('Unable to retrieve user list.'),
                              ignore=True)

        users = SortedDict([(user.id, user) for user in users])
        return users.values()

class AdminRecordView(tabs.TabbedTableView):
    tab_group_class = admin_tabs.RecordTabs
    template_name = 'admin/users/record.html'

class AdminDetailView(tables.DataTableView, forms.ModalFormView):
    table_class = admin_tables.SumptionDetailTable
    form_class = admin_forms.SumptionDetailForm
    template_name = 'admin/users/detail.html'

    def get_data(self):
        try:
            sumptions = api.proxy.resource_get(self.request,
                                               self.kwargs['user_id'],
                                               self.kwargs['source_name'],
                                               self.kwargs['source_id'])
        except Exception:
            sumptions = []
            exceptions.handle(self.request,
                              _('Unable to retrieve consumption list.'),
                              ignore=True)
        return sumptions

    @memoized.memoized_method
    def get_form(self):
        form_class = self.get_form_class()
        return super(AdminDetailView, self).get_form(form_class)

    def get_context_data(self, **kwargs):
        context = super(AdminDetailView, self).get_context_data(**kwargs)
        #context['form'] = self.get_form()
        if self.request.is_ajax():
            context['hide'] = True
        context['user_id'] = self.kwargs['user_id']
        return context
