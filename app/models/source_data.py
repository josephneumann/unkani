import hashlib
from datetime import datetime
from app import db
from app.models.extensions import BaseExtension
from sqlalchemy.dialects import postgresql
from app.main.errors import ValidationError


class SourceData(db.Model):
    """Raw data, stored as JSONb.
    If data already exists, raises SQLAlchemy IntegrityError"""
    __tablename__ = 'source_data'
    __mapper_args__ = {
        'extension': BaseExtension(),
    }

    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.Text, index=True)
    route = db.Column(db.Text, index=True)
    payload = db.Column(postgresql.JSONB)
    payload_hash = db.Column(db.Text, index=True)
    response = db.Column(postgresql.JSONB)
    status_code = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)

    def __repr__(self):  # pragma: no cover
        return '<SourceData {}:{}>'.format(self.id,self.route)

    def before_insert(self):
        payload_hash = hashlib.sha1(self.payload.encode('utf-8')).hexdigest()
        if self.query.filter(SourceData.payload_hash == payload_hash).first():
            raise ValidationError
        self.payload_hash = payload_hash

    def before_update(self):
        pass
