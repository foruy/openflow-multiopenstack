import datetime
import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
from oslo_utils import uuidutils
from six.moves.urllib import parse

from daoliproxy import agent
from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _
from daoliproxy.mail import main as mail_main
from daoliproxy import utils

CONF = cfg.CONF
CONF.import_opt('admin_port', 'daoliproxy.api.base')

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The authentication API controller.

    Including authentication, etc.
    """

    def _format_user(self, user, token=None):
        _user = {}
        _user['id'] = user.id
        _user['username'] = user.username
        _user['email'] = user.email
        _user['phone'] = user.phone
        _user['company'] = user.company
        _user['created_at'] = user.created_at
        _user['updated_at'] = user.updated_at

        if token is not None:
            _user['auth_token'] = token.id
            _user['expires'] = (token.created_at + datetime.timedelta(
                                seconds=CONF.auth_expires))
            _user['project_id'] = token.user_id

        return _user

    def authenticate(self, req, body):
        auth = self._from_body(body, 'auth')
        context = req.environ['proxy.context']
        kwargs = body.get('kwargs', {})
        if not kwargs:
            kwargs['user_agent'] = req.user_agent
            kwargs['user_addr'] = req.client_addr

        if 'username' not in auth or 'password' not in auth:
            msg = _("Username or password is not correct")
            raise exc.HTTPBadRequest(explanation=msg)

        try:
            user = self.db.authenticate(context,
                                        auth["username"],
                                        auth["password"],
                                        **kwargs)

        except exception.UserNotFound as e:
            raise exc.HTTPNotFound(explanation=e.message)

        token = self.db.user_token_create(context, user.id)

        return {'user': self._format_user(user, token)}

    def authenticate_by_zone(self, req, user_id, body):
        self._authenticate_by_zone(req, user_id, body)

    def authenticate_by_zone_proxy(self, req, user_id, body):
        self._authenticate_by_zone(req, user_id, body, checked=False)

    def _authenticate_by_zone(self, req, user_id, body, checked=False):
        auth = self._from_body(body, 'auth')
        context = req.environ['proxy.context']

        zone = self.db.zone_get(context, auth['zone_id'])
        if not zone or zone.disabled:
            msg = _("Zone could not be found or disabled.")
            raise exc.HTTPNotFound(explanation=msg)

        user = self.db.user_get(context, user_id)
        if not user:
            msg = _("User could not be found or disabled.")
            raise exc.HTTPNotFound(explanation=msg)

        # proxy -> authentication_by_zone_proxy
        if checked and zone.idc_id != CONF.idc_id:
            #services = self.db.service_get_by_idc(context, zone.idc_id)
            #if len(services) < 1:
            #    msg = _("Availiable idc could not be found.")
            #    raise exc.HTTPNotFound(explanation=msg)

            #context.auth_url = services[0].url
            #agent.authentication_by_zone_proxy(context, user_id, zone.id)
            self.proxy_method('authentication_by_zone_proxy',
                     context, zone.idc_id, user_id, zone.id)
        else:
            #try:
            self._authenticate(context, user, zone)
            #except (exception.keystoneclient.AuthorizationFailure,
            #         exception.keystoneclient.Unauthorized) as e:
            #    raise exc.HTTPNotFound(explanation=e)

    def user_absolute_limits(self, req):
        context = req.environ['proxy.context']

        limits = self.db.user_absolute_limits(context,
                context.user_id, zone_id=req.GET.get('zone_id'))

        return {'limits': limits}

    def list(self, req):
        context = req.environ['proxy.context']
        users = [self._format_user(user) for user in \
                 self.db.user_get_all(context)]

        return {'users': users}

    def get(self, req, id):
        context = req.environ['proxy.context']
        user = self._format_user(self.db.user_get(context, id))
        return {'user': user}

    def delete(self, req, id):
        context = req.environ['proxy.context']

        try:
            self.db.role_get_by_name(context, context.user_id)
        except exception.AdminRequired as e:
            raise exc.HTTPForbidden(explanation=e)

        user = self.db.user_get(context, id)

        for zone in self.db.zone_get_all(context):
            zone.auth_url = utils.replace_url(
                    zone.auth_url, port=CONF.admin_port)
            try:
                for keyuser in agent.user_list(zone):
                    if keyuser.username == user.username:
                        agent.user_delete(zone, keyuser.id)
                        agent.tenant_delete(zone, keyuser.tenantId)
            except exception.keystoneclient.NotFound:
                pass

        self.db.user_delete(context, id)
        return webob.Response(status=202)

    @wsgi.action('os-check')
    def check(self, req, body):
        data = self._from_body(body, 'os-check')
        context = req.environ['proxy.context']

        for key, val in data.items():
            if (key == 'username' and val in utils.USER_FILTERS) or \
                    self.db.user_check(context, key, val):
                msg = _('The %s "%s" is already in used.' % (key, val))
                raise exc.HTTPConflict(explanation=msg)

    def _send_mail(self, context, auth):
        recs = [{'email': auth['email'],
                 'subject': 'Welcome to Register Daolicloud',
                 'body': mail_main.render('register', **auth)}]

        subject = 'New User: %s [%s]' % (auth['username'], auth['email'])

        for contact in CONF.email_cc:
            recs.append({'email': contact, 'subject': subject,
                         'body': mail_main.render('register_cc', **auth)})

        try_count = 1
        while try_count > 0:
            try_count -= 1
            try:
                return mail_main.send(recs)
            except Exception as e:
                excep = e

        if try_count <= 0:
            auth['message'] = excep.message
            self.db.user_task(context, 'sendmail', json.dumps(auth))
            raise excep

    def register(self, req, body):
        auth = self._from_body(body, 'auth')
        context = req.environ['proxy.context']

        if auth['username'] in utils.USER_FILTERS or \
                self.db.user_check(context, 'username', auth['username']):
            msg = _('The username "%s" is already in used.' % auth['username'])
            raise exc.HTTPConflict(explanation=msg)

        if not auth.get('password', None):
            auth['password'] = utils.generate_password()

        user = self.db.register(context,
                                username=auth['username'],
                                password=auth['password'],
                                email=auth['email'],
                                type=auth['type'],
                                phone=auth['phone'],
                                company=auth['company'],
                                reason=auth['reason'])

        self.add_thread(self._send_mail, context, auth)
        #self._send_mail(context, auth)
        LOG.debug('User %s[%s] send successfully!' % (
                auth['username'], auth['email']))

        for zone in self.db.zone_get_all(context):
            self.add_thread(self._register_thread, context, zone, user)

        return {'user': user}

    def register_proxy(self, req, body):
        auth = self._from_body(body, 'auth')
        context = req.environ['proxy.context']

        user = self.db.user_get(context, auth['user_id'])
        zone = self.db.zone_get(context, auth['zone_id'])
        self._register_thread(context, zone, user, checked=False)

        return {'user': user}

    def validate(self, req, body):
        user = self._from_body(body, 'user')
        context = req.environ['proxy.context']

        if not self.db.validate_user(context, user):
            msg = _('The user "%s" does not match.')
            raise exc.HTTPNotFound(explanation=(msg % user.get('username')))

    def update_key(self, req, body):
        user = self._from_body(body, 'user')
        context = req.environ['proxy.context']

        if not user['kwargs'].get('key', None):
            user['kwargs']['key'] = uuidutils.generate_uuid()

        user_obj = self.db.update_user(context, user['base'],
                extra={'key': user['kwargs']['key']})

        qparams = {'uid': user_obj.id,
                   'username': user['base']['username'],
                   'email': user['base']['email'],
                   'tid': user['kwargs']['key']}

        url = "%s?%s" % (user['kwargs']['url'], parse.urlencode(qparams))

        recv = {'email': user['base']['email'],
                'subject': '[Daolicloud] Reset your password!',
                'body': mail_main.render('getpassword',
                                         url=url,
                                         **user['base'])}

        mail_main.send([recv])
        return webob.Response(status=202)

    def getpassword(self, req, body):
        user = self._from_body(body, 'user')
        context = req.environ['proxy.context']

        self._getpassword(context, user['base'], user['kwargs']['key'])
        return webob.Response(status=202)

    def _getpassword(self, context, user, key):
        user_obj = self.db.validate_user(context, user)

        if not user_obj:
            msg = _("User not found.")
            raise exc.HTTPNotFound(explanation=msg)

        if not user_obj['extra'] or key != user_obj['extra']['key']:
            msg = _("Request expired.")
            raise exc.HTTPForbidden(explanation=msg)

    def resetpassword(self, req, body):
        user = self._from_body(body, 'user')
        context = req.environ['proxy.context']

        self._getpassword(context, user['base'], user['kwargs']['key'])
        password = user['kwargs']['password']

        user_obj = self.db.update_user(context, user['base'],
                password=password, extra={})

        for zone in self.db.zone_get_all(context):
            # proxy -> resetpassword_proxy
            if zone.idc_id != CONF.idc_id:
                return self.proxy_method('resetpassword_proxy',
                        context, zone.idc_id, zone_id=zone.id,
                        username=user_obj.username,
                        password=password)
            else:
                self._resetpassword(context, zone, user_obj.username, password)

        return webob.Response(status=202)

    def _resetpassword(self, context, zone, username, password):
        zone.auth_url = utils.replace_url(
                zone.auth_url, port=CONF.admin_port)
        try:
            for keyuser in agent.user_list(zone):
                if keyuser.username == username:
                    agent.user_update_password(zone, keyuser.id, password)
                    break
        except Exception as e:
            data = {'auth': zone, 'message': e.message,
                    'password': password, 'user': username}
            self.db.user_task(context, 'resetpassword', json.dumps(data))

        return webob.Response(status=202)

    def resetpassword_proxy(self, req, body):
        user = self._from_body(body, 'user')
        context = req.environ['proxy.context']

        zone = self.db.zone_get(context, user['zone_id'])
        if not zone:
            msg = _("Zone could not be found.")
            raise exc.HTTPNotFound(explanation=msg)

        self._resetpassword(context, zone, user['username'], user['password'])

        return webob.Response(status=202)


    def login_list(self, req):
        context = req.environ['proxy.context']
        
        user_id = req.GET.get('user_id', None)
        if not user_id:
            user_id = context.user_id

        users = self.db.user_login_list(context, user_id=user_id)
        return {'users': users}

def create_resource():
    return wsgi.Resource(Controller())
