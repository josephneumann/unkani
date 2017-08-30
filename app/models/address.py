from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.utils.general import json_serial
from app.models.extensions import BaseExtension
import hashlib, json, re


class Address(sa.Model):
    _tablename__ = 'address'
    __mapper_args__ = {'extension': BaseExtension()}
    id = sa.Column(sa.Integer, primary_key=True)
    address1 = sa.Column("address1", sa.Text)
    address2 = sa.Column("address2", sa.Text)
    city = sa.Column("city", sa.Text)
    state = sa.Column("state", sa.String(2))
    zipcode = sa.Column("zipcode", sa.Text, index=True)
    primary = sa.Column("primary", sa.Boolean)
    active = sa.Column("active", sa.Boolean, default=True)
    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'), index=True)
    patient = sa.relationship("Patient", back_populates="addresses")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), index=True)
    user = sa.relationship("User", back_populates="addresses")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    address_hash = sa.Column(sa.Text)
    row_hash = sa.Column(sa.Text)

    def __init__(self, address1=None, address2=None, city=None, state=None, zipcode=None, active=True, primary=False,
                 user_id=None, patient_id=None, **kwargs):
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.active = active
        self.primary = primary
        self.user_id = user_id
        self.patient_id = patient_id

    def dump(self):
        schema = AddressSchema()
        return schema.dump(self).data

    def generate_row_hash(self):
        data = {"address1": self.address1, "address2": self.address2, "city": self.city,
                "state": self.state, "zipcode": self.zipcode,
                "patient_id": self.patient_id, "user_id": self.user_id}
        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def generate_address_hash(self):
        address1 = self.address1
        if not address1:
            address1 = ''
        address2 = self.address2
        if not address2:
            address2 = ''
        address_lines = str(address1 + address2)
        data = {"address_lines": address_lines, "city": self.city,
                "state": self.state, "zipcode": self.zipcode}
        for key in data:
            if isinstance(data[key], str):
                # Remove punctuation and whitespace from strings in address to hash
                data[key] = re.sub(r'[^a-zA-Z0-9]', '', data[key])
        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()
        self.address_hash = self.generate_address_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()
        self.address_hash = self.generate_address_hash()


class AddressSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy Address model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    id = fields.Integer(attribute='id')
    address1 = fields.String(attribute='address1')
    address2 = fields.String(attribute='address2')
    city = fields.String(attribute='city')
    state = fields.String(attribute='state')
    zipcode = fields.String(attribute='zipcode')
    primary = fields.Boolean(attribute='primary')
    active = fields.Boolean(attribute='active')
    patient_id = fields.Integer(attribute='patient_id')
    user_id = fields.Integer(attribute='user_id')
    created_at = fields.DateTime(attribute='created_at')
    updated_at = fields.DateTime(attribute='updated_at')
    address_hash = fields.String(attribute='address_hash')
    row_hash = fields.String(attribute='row_hash')

    @post_load
    def make_address(self, data):
        return Address(**data)
