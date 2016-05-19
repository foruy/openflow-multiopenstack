import logging

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from .exceptions import KeystoneAuthException

LOG = logging.getLogger(__name__)

class Login(AuthenticationForm):
    """ Form used for logging in a user. """
    username = forms.CharField(label=_("User Name"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False))

    @sensitive_variables()
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not (username and password):
            # Don't authenticate, just let the other validators handle it.
            return self.cleaned_data

        try:
            self.user_cache = authenticate(request=self.request,
                                           username=username,
                                           password=password)

            msg = 'Login successful for user "%(username)s".' % \
                {'username': username}
            LOG.info(msg)
        except KeystoneAuthException as exc:
            msg = 'Login failed for user "%(username)s".' % \
                {'username': username}
            LOG.warning(msg)
            self.request.session.flush()
            raise forms.ValidationError(exc)

        if hasattr(self, 'check_for_test_cookie'): # Dropped in django 1.7
            self.check_for_test_cookie()
        return self.cleaned_data
