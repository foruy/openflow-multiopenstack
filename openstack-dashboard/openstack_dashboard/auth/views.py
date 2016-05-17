from django import shortcuts
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

import horizon
from horizon import forms
from horizon import exceptions
from horizon import messages

from openstack_dashboard.auth.forms import GetPasswordForm
from openstack_dashboard.auth.forms import ResetPasswordForm
from openstack_dashboard.utils import proxyclient

class GetPasswordView(forms.ModalFormView):
    form_class = GetPasswordForm
    template_name = 'auth/getpassword.html'
    success_url = reverse_lazy('message')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return shortcuts.redirect(horizon.get_user_home(request.user))
        return super(GetPasswordView, self).get(request, *args, **kwargs)

class ResetPasswordView(forms.ModalFormView):
    form_class = ResetPasswordForm
    template_name = 'auth/passwordreset.html'
    success_url = reverse_lazy('message')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return shortcuts.redirect(horizon.get_user_home(request.user))
        uid = self.request.REQUEST.get('uid')
        tid = self.request.REQUEST.get('tid')
        email = self.request.REQUEST.get('email')
        username = self.request.REQUEST.get('username')
        if not (uid and tid and email and username):
            raise exceptions.Http302(reverse('getpassword'))
        try:
            proxyclient().users.getpassword(uid, username, email, key=tid)
        except:
            msg = _("Request expired.")
            exceptions.handle(self.request, msg, redirect=self.success_url)
        return super(ResetPasswordView, self).get(request, *args, **kwargs)

def message(request):
    template_name = "message.html"
    if not request._messages._loaded_messages:
        redirect_to = reverse('login')
        return HttpResponseRedirect(redirect_to)
    return TemplateResponse(request, template_name)

#def activate(request, user_id):
#    uid = self.request.REQUEST.get('uid')
#    template_name = "message.html"
#    username = request.REQUEST.get('username')
#    hemail = request.REQUEST.get('email')
#    try:
#        api.proxy.validate_user(request, username, hemail)
#        user = api.proxy.getpassword(request, uid, username, hemail)
#    except:
#        messages.error(request, _("Request expired."))
#        return TemplateResponse(request, template_name)
#    api.resetpassword(request, user_id,username, hemail)
#    messages.success(request,
#                     _('User "%s" was successfully activated.')
#                     % username)
#
#    return TemplateResponse(request, template_name)
