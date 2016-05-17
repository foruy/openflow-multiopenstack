"""
security_groups interface
"""
from six.moves.urllib import parse

from proxyclient import base

class SecurityGroup(base.Resource):
    pass

class SecurityGroupManager(base.Manager):
    resource_class = SecurityGroup

    def list(self, search_opts=None):
        if search_opts is None:
            search_opts = {}

        qparams = {}
        for opt, val in search_opts.iteritems():
            if val: qparams[opt] = val

        query_string = "?%s" % parse.urlencode(qparams) if qparams else ""

        return self._get('/security_groups%s' % query_string,
                         'security_groups')

    def update(self, **kwargs):
        body = {'security_group': kwargs}
        return self._update('/security_groups', body)
