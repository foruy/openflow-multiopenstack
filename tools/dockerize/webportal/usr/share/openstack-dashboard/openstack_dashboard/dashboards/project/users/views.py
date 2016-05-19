from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.users \
    import forms as project_forms
from openstack_dashboard.dashboards.project.users \
    import tables as project_tables
from openstack_dashboard.dashboards.project.users \
    import tabs as project_tabs

class IndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.RecordTabs
    template_name = 'project/users/record.html'

class DetailView(tables.DataTableView, forms.ModalFormView):
    table_class = project_tables.SumptionDetailTable
    form_class = project_forms.SumptionDetailForm
    template_name = 'project/users/detail.html'

    def get_data(self):
        try:
            sumptions = api.proxy.resource_get(self.request,
                                               source_name=self.kwargs['source_name'],
                                               source_id=self.kwargs['source_id'])
        except Exception:
            sumptions = []
            exceptions.handle(self.request,
                              _('Unable to retrieve consumption list.'),
                              ignore=True)
        return sumptions

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        if self.request.is_ajax():
            context['hide'] = True
        return context
