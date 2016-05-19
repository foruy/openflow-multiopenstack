from sqlalchemy import Text
from sqlalchemy import types as sql_types

from daoliagent.openstack.common import jsonutils

class JsonBlob(sql_types.TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return jsonutils.dumps(value)

    def process_result_value(self, value, dialect):
        return jsonutils.loads(value)
