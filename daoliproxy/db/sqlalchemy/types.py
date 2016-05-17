"""Custom SQLAlchemy types."""
from oslo_serialization import jsonutils

from sqlalchemy import Text
from sqlalchemy import types

class JsonBlob(types.TypeDecorator):

    impl = Text

    def process_bind_param(self, value, dialect):
        return jsonutils.dumps(value)

    def process_result_value(self, value, dialect):
        return jsonutils.loads(value)
