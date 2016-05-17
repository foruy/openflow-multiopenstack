import logging
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import messages
from horizon import exceptions
from horizon.utils import validators as utils_validators

from openstack_dashboard import api
from openstack_dashboard import exceptions as _exceptions
from openstack_dashboard.dashboards.project.network_edges.utils \
    import limit_port_range

LOG = logging.getLogger(__name__)

class FirewallForm(forms.SelfHandlingForm):
    required_css_class = 'required form-float'

    gateway_ip = forms.ChoiceField(label=_("Select Gateway"),
                                   widget=forms.SelectWidget(attrs={'style': 'width:220px'}))
    gateway_port = forms.IntegerField(label=_("Gateway Port (10000-50000)"),
                                    validators=[limit_port_range],
                                    widget=forms.TextInput(attrs={'style': 'width:210px'}))
    service_port = forms.IntegerField(label=_("Service Port"), min_value=1,
                                    validators=[utils_validators.validate_port_range],
                                    widget=forms.TextInput(attrs={'style': 'width:210px'}))

    def __init__(self, request, *args, **kwargs):
        super(FirewallForm, self).__init__(request, *args, **kwargs)
        choices = []

        for gateway in kwargs['initial']['gateways']:
            choices.append((gateway.hostname, gateway.vext_ip))
        #choices = [(gateway.hostname, gateway.ext_ip) for gateway in gateways]

        if choices:
            choices.insert(0, ("", _("Select Gateway")))
        else:
            choices.insert(0, ("", _("No Gateway available")))
        self.fields['gateway_ip'].choices = choices

    def clean(self):
        data = super(forms.Form, self).clean()
        hostname = data.get("gateway_ip")
        gateway_port = data.get("gateway_port")
        service_port = data.get("service_port")
        if hostname and gateway_port and service_port:
            instance = self.initial['instance']
            try:
                api.proxy.firewall_exist(self.request,
                                         instance.id,
                                         hostname=hostname,
                                         gateway_port=gateway_port)
            except _exceptions.Conflict:
                msg = _("This gateway port already be used.")
                raise forms.ValidationError(msg)

        return data

    def handle(self, request, data):
        hostname = data['gateway_ip']
        gport = data['gateway_port']
        sport = data['service_port']
        instance = self.initial['instance']
        try:
            firewall = api.proxy.firewall_create(
                    request, instance.id, hostname, gport, sport)
            message = _('Create gateway %(gport)s, service %(sport)s to '
                         ' instance %(inst)s.') % {"gport": gport,
                                                   "sport": sport,
                                                   "inst": instance.name}
            messages.success(request, message)
            return firewall
        except Exception:
            redirect = reverse("horizon:project:network_edges:index")
            exceptions.handle(request,
                              _('Unable to add firewall.'),
                              redirect=redirect)
