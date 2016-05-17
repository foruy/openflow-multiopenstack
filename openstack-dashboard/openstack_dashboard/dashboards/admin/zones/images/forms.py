from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import exceptions

from openstack_dashboard import api

class RebuildForm(forms.SelfHandlingForm):
    def handle(self, request, data):
        try:
            api.proxy.image_rebuild(request, self.initial['zone_id'])
        except Exception:
            exceptions.handle(request, _('Unable to rebuild images.'))
        return True

