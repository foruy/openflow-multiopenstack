import json
import logging

import django
from django import shortcuts
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views as django_auth_views
from django.http import HttpResponse
from django.utils.functional import curry
import django.views.decorators.vary
from django.views.decorators.cache import never_cache  # noqa
from django.views.decorators.csrf import csrf_protect  # noqa
from django.views.decorators.debug import sensitive_post_parameters
from django.template.response import TemplateResponse

import horizon
from horizon import base
from horizon import exceptions
from horizon.views import APIView

from openstack_dashboard import api
from openstack_dashboard import validators
from openstack_dashboard.forms import Login
from openstack_dashboard.user import set_session_from_user

LOG = logging.getLogger(__name__)

def get_user_home(user):
    dashboard = None
    if user.is_superuser:
        try:
            dashboard = horizon.get_dashboard('admin')
        except base.NotRegistered:
            pass

    if dashboard is None:
        dashboard = horizon.get_default_dashboard()

    return dashboard.get_absolute_url()

@django.views.decorators.vary.vary_on_cookie
def splash(request):
    if not request.user.is_authenticated():
        raise exceptions.NotAuthenticated()

    response = shortcuts.redirect(horizon.get_user_home(request.user))
    if 'logout_reason' in request.COOKIES:
        response.delete_cookie('logout_reason')
    return response

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name=None, extra_context=None, **kwargs):
    """Logs a user in using the :class:`~openstack_auth.forms.Login` form."""
    # If the user is already authenticated, redirect them to the
    # dashboard straight away, unless the 'next' parameter is set as it
    # usually indicates requesting access to a page that requires different
    # permissions.
    if (request.user.is_authenticated() and
            auth.REDIRECT_FIELD_NAME not in request.GET and
            auth.REDIRECT_FIELD_NAME not in request.POST):
        return shortcuts.redirect(settings.REDIRECT_URL)

    if request.method == "POST":
        if django.VERSION >= (1, 6):
            form = curry(Login)
        else:
            form = curry(Login, request)
    else:
        form = curry(Login, initial={})

    if extra_context is None:
        extra_context = {'redirect_field_name': auth.REDIRECT_FIELD_NAME}

    extra_context['lang'] = request.session.get(settings.LANGUAGE_COOKIE_NAME,
            request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME,
                                request.LANGUAGE_CODE))

    if not template_name:
        if request.is_ajax():
            template_name = 'auth/_login.html'
            extra_context['hide'] = True
        else:
            template_name = 'auth/login.html'

    res = django_auth_views.login(request,
                                  template_name=template_name,
                                  #redirect_field_name='n',
                                  authentication_form=form,
                                  extra_context=extra_context,
                                  **kwargs)
    # Set the session data here because django's session key rotation
    # will erase it if we set it earlier.
    if request.user.is_authenticated():
        set_session_from_user(request, request.user)
    return res

def proxy_logout(request):
    try:
        api.proxy.logout(request)
    except Exception as e:
        LOG.info(e)

def logout(request, login_url=None, **kwargs):
    """Logs out the user if he is logged in. Then redirects to the log-in page.

    .. param:: login_url

       Once logged out, defines the URL where to redirect after login

    .. param:: kwargs
       see django.contrib.auth.views.logout_then_login extra parameters.

    """
    msg = 'Logging out user "%(username)s".' % \
        {'username': request.user.username}
    LOG.info(msg)
    #proxy_logout(request)
    return django_auth_views.logout_then_login(request, login_url=login_url,
                                               **kwargs)

def index(request):
    if not request.user.is_authenticated():
        return shortcuts.redirect(settings.REDIRECT_URL)

    if request.method == 'POST':
        api.proxy.authenticate_by_zone(request, request.POST['zone'])
        return HttpResponse(status=200)

    if not request.session.has_key('status'):
        return shortcuts.redirect(settings.REDIRECT_URL)

    del request.session['status']
    zones = [zone for zone in api.proxy.availability_zone_list(request, True)
             if not zone.disabled]
    return TemplateResponse(request, 'index.html', context={'zones': zones})

def checkdata(request):
    post_data = json.loads(request.body)
    post_data['check_dest'] = post_data['check_dest'].strip()
    response_data = {'id': post_data['id'], 'status': 200}

    try:
        validators.check_data(post_data['checkonly_type'], post_data['check_dest'])
        if post_data['checkonly_type'] == 'email' and \
            validators.check_ignore(post_data['check_dest']):
            LOG.info('Redirect email "%s"' % post_data['check_dest'])
        else:
            api.proxy.checkdata(request, post_data['checkonly_type'], post_data['check_dest'])
    except:
        response_data['status'] = 400

    response = HttpResponse(content_type='application/json')
    response.write(json.dumps(response_data))
    response.flush()
    return response

def register(request):
    if request.method == 'POST':
        data, errors = validators.validate_data(json.loads(request.body))
        if errors:
            return shortcuts.render(request, 'auth/pc_register_en.html',
                    {'data': data, 'errors': errors}, status=400)
        user = api.proxy.register(request, username=data['username'], password=data['password'],
                                  email=data['email'], type=0, phone=data['phone'],
                                  company=data['company'], reason=data['reason'])
        request.session.clear()
        request.session.set_test_cookie()
        return HttpResponse(status=200)
    else:
        return TemplateResponse(request, 'pc_register_en.html')

def jump(request):
    return TemplateResponse(request, 'jump.html')
