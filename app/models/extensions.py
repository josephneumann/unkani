from app import db
from datetime import datetime


class BaseExtension(db.MapperExtension):
    __doc__ = """Base extension class for all sa model entities"""

    def before_insert(self, mapper, connection, target):
        now = datetime.utcnow()
        target.created_at = now
        target.updated_at = now
        target.before_insert()

    def before_update(self, mapper, connection, target):
        now = datetime.utcnow()
        target.updated_at = now
        target.before_update()
