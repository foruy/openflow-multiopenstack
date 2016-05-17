from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import exceptions

from openstack_dashboard import api

class ZoneForm(forms.SelfHandlingForm):
    #id = forms.CharField(label=_("Openstack Id"), max_length=255)
    name = forms.CharField(label=_("Openstack Name"), max_length=255)
    auth_url = forms.CharField(label=_("Keystone Auth URL"))
    token = forms.CharField(label=_("Keystone Token"))
    default_instances = forms.IntegerField(label=_("Default Quota"),
                                           required=False,
                                           initial=10,
                                           min_value=1)

    def handle(self, request, data):
        try:
            #zone = api.proxy.zone_create(request, id=data['id'], name=data['name'],
            zone = api.proxy.zone_create(request, id=None, name=data['name'],
                                         auth_url=data['auth_url'], auth_token=data['token'],
                                         default_instances=data['default_instances'])
        except Exception:
            redirect = reverse("horizon:admin:zones:index")
            exceptions.handle(request,
                              _('Unable to add openstack zone.'),
                              redirect=redirect)
        try:
            api.proxy.image_rebuild(request, zone.id)
        except Exception:
            exceptions.handle(request, _('Unable to rebuild images.'), ignore=True)
        try:
            api.proxy.flavor_rebuild(request, zone.id)
        except Exception:
            exceptions.handle(request, _('Unable to rebuild flavors.'), ignore=True)
        try:
            api.proxy.gateway_rebuild(request, zone.id)
        except Exception:
            exceptions.handle(request, _('Unable to rebuild gateways.'), ignore=True)

        return True
