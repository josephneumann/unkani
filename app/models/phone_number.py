from app import db, ma
from marshmallow import fields
from datetime import datetime

from app.utils.demographics import validate_phone, validate_contact_type, format_phone
from app.models.extensions import BaseExtension
import hashlib, json


##################################################################################################
# Phone Number SQL Alchemy Model
##################################################################################################
class PhoneNumber(db.Model):
    __tablename__ = 'phone_number'
    __versioned__ = {}
    __mapper_args__ = {'extension': BaseExtension()}

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column("number", db.Text)
    type = db.Column("type", db.Text)
    active = db.Column(db.Boolean, default=True)
    primary = db.Column(db.Boolean, default=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), index=True)
    patient = db.relationship("Patient", back_populates="phone_numbers")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    user = db.relationship("User", back_populates="phone_numbers")
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)
    row_hash = db.Column(db.Text, index=True)

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


class PhoneNumberAPI:
    def __init__(self, number=None, type=None, active=True, primary=False, user_id=None, patient_id=None):
        self.errors = {"critical": {},
                       "warning": {}}
        self._phone_number = None

        self.number = number
        self.type = type
        self.active = active
        self.primary = primary


        # TODO Handle user and patient attributes with API
        self.user_id = user_id
        self.user = None

        self.patient_id = patient_id
        self.patient = None

    @property
    def phone_number(self):
        if self._phone_number:
            return self._phone_number
        else:
            return None

    @phone_number.setter
    def phone_number(self, phone_number):
        if phone_number is None:
            pass
        elif isinstance(phone_number, PhoneNumber):
            self._phone_number = phone_number
        else:
            raise TypeError('Object assigned to user was not a SQL Alchemy PhoneNumber type object.')

    def loads_json(self, data):

        pd = None

        if isinstance(data, dict):
            pd = data
        else:
            try:
                pd = json.loads(data)
            except:
                self.errors['critical']['json decode error'] = 'An error occurred when attempting to decode JSON.'
        if pd:
            self.number = pd.get('number', None)
            self.type = pd.get('type', None)
            self.active = pd.get('active', True)
            self.primary = pd.get('active', False)

            self.user_id = pd.get('user_id', None)
            self.patient_id = pd.get('patient_id', None)

    def validate_number(self):
        if self.number:
            try:
                self.number = validate_phone(self.number)
            except ValueError as e:
                self.errors['critical']['phone number'] = e.args[0]
                self.number = None

    def validate_type(self):
        if self.type:
            try:
                self.type = validate_contact_type(type=self.type)
            except ValueError as e:
                self.errors['critical']['phone number type'] = e.args[0]
                self.type = None
        else:
            self.type = None

    def validate_active(self):
        if isinstance(self.active, bool):
            self.active = self.active
        else:
            self.active = None

    def validate_primary(self):
        if isinstance(self.primary, bool):
            pass
        else:
            self.primary = None

    def run_validations(self):
        self.validate_number()
        self.validate_type()
        self.validate_active()
        self.validate_primary()

    def run_permission_checks(self):
        pass

    def make_object(self):

        if self.errors['critical']:
            return None, self.errors

        else:
            if isinstance(self.phone_number, PhoneNumber):
                pn = self.phone_number
            else:
                pn = PhoneNumber()

            pn.number = self.number
            pn.type = self.type
            if isinstance(self.active, bool):
                pn.active = self.active
            pn.active = self.active
            pn.primary = self.primary

            self.phone_number = pn

            return self.phone_number, self.errors