from django.core.urlresolvers import reverse

from horizon import forms

from openstack_dashboard.dashboards.admin.zones.gateways \
    import forms as gateway_forms

class RebuildView(forms.ModalFormView):
    form_class = gateway_forms.RebuildForm
    template_name = 'admin/zones/gateways/rebuild.html'
    success_url = 'horizon:admin:zones:detail'

    def get_success_url(self):
        return reverse(self.success_url, args=(self.kwargs["zone"],))

    def get_initial(self):
        return {"zone_id": self.kwargs["zone"]}

    def get_context_data(self, **kwargs):
        context = super(RebuildView, self).get_context_data(**kwargs)
        context['zone_id'] = self.kwargs["zone"]
        return context
