from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates

from app.utils import normalize_address
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


class AddressAPI:
    def __init__(self, address1=None, address2=None, city=None, state=None, zipcode=None, primary=False, active=True,
                 patient_id=None, user_id=None):
        self.errors = {"critical": {},
                       "warning": {}}
        self._address = None

        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.active = active
        self.primary = primary

        self.patient_id = patient_id
        self.user_id = user_id

    @property
    def address(self):
        if self._address:
            return self._address
        else:
            return None

    @address.setter
    def address(self, address):
        if address is None:
            pass
        elif isinstance(address, Address):
            self._address = address
        else:
            raise TypeError('Object assigned to user was not a SQL Alchemy Address type object.')

    def loads_json(self, data):

        d = None

        if isinstance(data, dict):
            d = data
        else:
            try:
                d = json.loads(data)
            except:
                self.errors['critical']['json decode error'] = 'An error occurred when attempting to decode JSON.'
        if d:
            self.address1 = d.get('address1', None)
            self.address2 = d.get('address2', None)
            self.city = d.get('city', None)
            self.state = d.get('state', None)
            self.zipcode = d.get('zipcode', None)
            self.primary = d.get('primary', False)
            self.active = d.get('active', True)

            self.patient_id = d.get('patient_id', None)
            self.user_id = d.get('user_id', None)

    def validate_address(self):
        addr_dict = normalize_address(address1=self.address1, address2=self.address2,
                                      city=self.city, state=self.state, zipcode=self.zipcode)

        self.address1 = addr_dict.get('address1', None)
        self.address2 = addr_dict.get('address2', None)
        self.city = addr_dict.get('city', None)
        self.state = addr_dict.get('state', None)
        self.zipcode = addr_dict.get('zipcode', None)

    def validate_active(self):
        if not isinstance(self.active, bool):
            self.active = None

    def validate_primary(self):
        if not isinstance(self.primary, bool):
            self.active = None

    def run_validations(self):
        self.validate_address()
        self.validate_active()
        self.validate_primary()

    def make_object(self):

        if self.errors['critical']:
            return None, self.errors

        else:
            if isinstance(self.address, Address):
                a = self.address
            else:
                a = Address()

            if self.address1:
                a.address1 = self.address1
            if self.address2:
                a.address2 = self.address2
            if self.city:
                a.city = self.city
            if self.state:
                a.state = self.state
            if self.zipcode:
                a.zipcode = self.zipcode

            if self.user_id:
                a.user_id = self.user_id

            if self.patient_id:
                a.patient_id = self.patient_id

            if isinstance(self.active, bool):
                a.active = self.active

            if isinstance(self.primary, bool):
                a.primary = self.primary

            self.address = a

            return self.address, self.errors