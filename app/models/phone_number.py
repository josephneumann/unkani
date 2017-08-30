from app import sa, ma
from marshmallow import fields
from app.utils.demographics import *
from app.models.extensions import BaseExtension
import hashlib, json


##################################################################################################
# Phone Number SQL Alchemy Model
##################################################################################################
class PhoneNumber(sa.Model):
    __tablename__ = 'phone_number'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True)
    number = sa.Column("number", sa.Text)
    type = sa.Column("type", sa.Text)
    active = sa.Column(sa.Boolean, default=True)
    primary = sa.Column(sa.Boolean, default=False)

    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'), index=True)
    patient = sa.relationship("Patient", back_populates="phone_numbers")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), index=True)
    user = sa.relationship("User", back_populates="phone_numbers")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text, index=True)

    def __init__(self, number=None, type=None, active=True, primary=False, user_id=None, patient_id=None, **kwargs):
        self.number = number
        self.type = type
        self.active = active
        self.primary = primary
        self.user_id = user_id
        self.patient_id = patient_id

    def generate_row_hash(self):
        data = {"number": self.number, "type": self.type, "active": self.active}
        for key in data:
            data[key] = str(data[key])
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()

    @property
    def formatted_phone(self):
        if self.number:
            return format_phone(self.number)



class PhoneNumberSchema(ma.Schema):
    """
    Marshmallow schema, associated with SQLAlchemy PhoneNumber model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines basic data type validation of attributes on de-serialization"""
    id = fields.Integer(attribute='id', dump_only=True)
    number = fields.String(attribute='number', dump_only=True)
    type = fields.String(attribute='type', dump_only=True)
    active = fields.Boolean(attribute='active', dump_only=True)
    user_id = fields.Integer(attribute='user_id', dump_only=True)
    patient_id = fields.Integer(attribute='patient_id', dump_only=True)
    created_at = fields.DateTime(attribute='created_at', dump_only=True)
    updated_at = fields.DateTime(attribute='updated_at', dump_only=True)
    row_hash = fields.String(attribute='row_hash', dump_only=True)
