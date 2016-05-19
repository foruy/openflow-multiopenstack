from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms

from openstack_dashboard import api

class SettingForm(forms.SelfHandlingForm):
    hostname = forms.CharField(widget=forms.HiddenInput())
    vext_ip = forms.CharField(label=_("Public IP"))
    disabled = forms.BooleanField(required=False,
                                  widget=forms.HiddenInput())

    msg = _('Open/Close Gateway')

    def __init__(self, request, *args, **kwargs):
        super(SettingForm, self).__init__(request, *args, **kwargs)
        gateway = kwargs['initial']['gateway']
        self.fields['vext_ip'].initial = gateway.vext_ip
        self.fields['disabled'].initial = gateway.disabled

    def handle(self, request, data):
        vext_ip = data['vext_ip']
        disabled = data.get('disabled') or False
        try:
            api.proxy.gateway_update(request,
                                     data['hostname'],
                                     vext_ip=vext_ip,
                                     disabled=disabled)
        except:
            redirect = reverse('horizon:admin:gateways:index')
            exceptions.handle(request, _("Unable to update gateway."),
                              redirect=redirect)

        return True
