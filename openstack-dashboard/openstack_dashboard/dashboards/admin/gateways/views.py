from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.gateways \
    import tables as gateway_tables
from openstack_dashboard.dashboards.admin.gateways \
    import forms as gateway_forms

class AdminIndexView(tables.DataTableView):
    table_class = gateway_tables.GatewaysTable
    template_name = 'admin/gateways/index.html'

    def get_data(self):
        instances = []
        try:
            gateways = api.proxy.gateway_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve gateways list.'))

        return gateways

class SettingView(forms.ModalFormView):
    form_class = gateway_forms.SettingForm
    template_name = 'admin/gateways/setting.html'
    success_url = reverse_lazy('horizon:admin:gateways:index')
    page_title = _("Setting Gateway")

    def get_context_data(self, **kwargs):
        context = super(SettingView, self).get_context_data(**kwargs)
        context['gateway_id'] = self.kwargs['id']
        return context

    def get_object(self, *args, **kwargs):
        gateway_id = self.kwargs['id']
        try:
            return api.proxy.device_get(self.request, gateway_id)
        except Exception:
            redirect = reverse("horizon:admin:gateways:index")
            msg = _('Unable to retrieve gateway details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(SettingView, self).get_initial()
        initial['devices'] = self.get_object()
        return initial
