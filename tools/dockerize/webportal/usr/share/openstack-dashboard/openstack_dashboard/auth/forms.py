import logging
import six.moves.urllib.parse as urlparse

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables
from django.core.urlresolvers import reverse

from horizon import messages
from horizon import exceptions
from horizon.utils import validators
from horizon.forms import SelfHandlingForm

from openstack_dashboard import api 

LOG = logging.getLogger(__name__)

class BaseForm(SelfHandlingForm):
    # We have to protect the entire "data" dict because it contains the
    # password and confirm password strings.
    @sensitive_variables('data', 'password')
    def clean(self):
        """Check to make sure password fields match."""
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise forms.ValidationError(_('Passwords do not match.'))
        return data

class GetPasswordForm(BaseForm):
    name = forms.CharField(label=_("User Name"))
    email = forms.EmailField(label=_("Email"))

    def clean(self):
        data = super(forms.Form, self).clean()
        username = data.get("name")
        email = data.get("email")
        if username and email:
            try:
                api.proxy.validate_user(self.request, username=username, email=email)
            except:
                msg = _("Username or email does not match.")
                raise forms.ValidationError(msg)
        return data

    def handle(self, request, data):
        hmail = data['email']
        username = data['name']

        url = urlparse.urlunparse((request.META['REQUEST_SCHEME'],
                                   request.get_host(),
                                   reverse('passwordreset'),
                                   None, None, None))
        try:
            api.proxy.update_user_key(request, username=username, email=hmail, url=url)
            messages.success(request, _("Please check your email and "
                                        "change your account password!"))
        except:
            exceptions.handle(request, _("Change password failed."),
                              redirect=reverse('message'))
        return True

class ResetPasswordForm(BaseForm):
    uid = forms.CharField(widget=forms.HiddenInput())
    username = forms.CharField(widget=forms.HiddenInput())
    email = forms.CharField(widget=forms.HiddenInput())
    tid = forms.CharField(widget=forms.HiddenInput())
    password = forms.RegexField(
        label=_("New Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        required=False,
        widget=forms.PasswordInput(render_value=False))

    def __init__(self, request, *args, **kwargs):
        super(ResetPasswordForm, self).__init__(request, *args, **kwargs)
        for attr in ('uid','username','email','tid'):
            self.fields[attr].initial = request.REQUEST.get(attr)
        self.fields['email'].widget = forms.TextInput(
                                       attrs={'readonly': 'readonly'})

    @sensitive_variables('data', 'password')
    def handle(self, request, data):
        try:
            api.proxy.resetpassword(request,
                                               data['uid'],
                                               data['username'],
                                               data['email'],
                                               key=data['tid'],
                                               password=data['password'])
            messages.success(request, _(
                'Your password has been updated successfully, '
                'Please login again.'))
        except Exception:
            exceptions.handle(request, _("Unable to update password."),
                              redirect=reverse('message'))
        return True
