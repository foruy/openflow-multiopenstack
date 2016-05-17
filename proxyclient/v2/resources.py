from proxyclient import base

class Resource(base.Resource):
    pass

class ResourceManager(base.Manager):

    resource_class = Resource

    def list(self, user_id=None):
        query_string = "?user_id=%s" % user_id if user_id else ""
        return self._list('/resources%s' % query_string, 'resources')

    def get(self, user_id, filters=None):
        if filters is None:
            filters = {}

        qparams = {}
        for opt, val in filters.iteritems():
            if val: qparams[opt] = val

        query_string = "?%s" % parse.urlencode(qparams) if qparams else ""

        return self._list('/resources/%s%s' % (user_id, query_string),
                          'resources')
