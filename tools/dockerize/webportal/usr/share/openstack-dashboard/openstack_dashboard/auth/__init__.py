from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import AnonymousUser
from horizon import exceptions
import logging
LOG = logging.getLogger(__name__)
#class User(AnonymousUser):
#    def __init__(self, user_domain_id=None, is_superuser=True):
#        LOG.error(dir([settings]))
#        self.id = getattr(settings, 'ADMIN_TOKEN')
#        if not self.id:
#            raise exceptions.NotAuthorized("Token not authorized")
#        self.user_domain_id = user_domain_id
#        self.is_superuser = is_superuser
#        self.authorized_tenants = []
#
#    def is_authenticated(self):
#        """ Checks for a valid token that has not yet expired. """
#        return self.id
#
#    @property
#    def token(self):
#        class Token:
#            def __init__(self, id):
#                self.id = id
#        return Token(self.id)

def send_email(receiver, subject, body):
    username = getattr(settings, 'EMAIL_HOST_USER')
    hostname = getattr(settings, 'EMAIL_HOST')
    if not hostname:
        raise exceptions.NotFound("Hostname not found")
    if not username:
        sender = hostname
    else:
        sender = username + '@' + hostname
    send_mail(subject, body, sender, [receiver], fail_silently=False)
