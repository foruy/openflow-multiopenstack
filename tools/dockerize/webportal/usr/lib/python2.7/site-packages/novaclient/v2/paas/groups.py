import six
from six.moves.urllib import parse

from novaclient import base

class SecurityGroup(base.Resource):
    def __str__(self):
        return str(self.id)

    def update(self):
        self.manager.update(self)

class SecurityGroupManager(base.ManagerWithFind):
    resource_class = SecurityGroup

    def list(self, search_opts=None):
        """Get a list of security groups."""
        search_opts = search_opts or {}

        qparams = dict((k, v) for (k, v) in six.iteritems(search_opts) if v)

        query_string = '?%s' % parse.urlencode(qparams) if qparams else ''

        return self._list('/os-daoli-groups%s' % query_string, 'groups')

    def update(self, project_id, **kwargs):
        """Update a security group."""
        body = {"group": kwargs}
        return self._update('/os-daoli-groups/%s' % project_id, body)
