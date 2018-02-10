from app import db, ma
from marshmallow import fields, ValidationError, post_load, validates

from app.utils import validate_email
from app.utils.demographics import *
from app.utils.general import json_serial
from app.models.extensions import BaseExtension
from fhirclient.models import contactpoint

import hashlib, json


##################################################################################################
# SQL ALCHEMY EMAIL ADDRESS MODEL DEFINITION
##################################################################################################

class EmailAddress(db.Model):
    __tablename__ = 'email_address'
    __versioned__ = {}
    __mapper_args__ = {'extension': BaseExtension()}

    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column("email", db.Text, index=True)
    primary = db.Column("primary", db.Boolean, default=False)
    active = db.Column("active", db.Boolean, default=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), index=True)
    patient = db.relationship("Patient", back_populates="email_addresses")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    user = db.relationship("User", back_populates="email_addresses")
    avatar_hash = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)
    row_hash = db.Column(db.Text, index=True)

    def __init__(self, email=None, primary=False, active=True):
        self.email = email
        self.primary = primary
        self.active = active
        self._fhir = None

    def generate_avatar_hash(self):
        __doc__ = """
        Generate an MD5 hash of the user's email.  Stores the result in the user
        'avatar_hash' attribute.  This value is used when constructing the gravatar URL."""
        if self.email and not re.search(r'(@EXAMPLE)+', self.email):
            email_lower = self.email.lower()
            self.avatar_hash = hashlib.md5(email_lower.encode('utf-8')).hexdigest()

    def gravatar_url(self, size=100, default='identicon', rating='g'):
        __doc__ = """
        Generate a Gravatar url based on an MD5 hash of the user's email. URL output
        conforms to standards for Globally Recognized Avatar service.
        Defaults established as:
         Size: 100px
         Default: identicon (if gravatar not found, pattern unique to MD5 hash is displayed\
         Rating: g
         """
        url = 'https://secure.gravatar.com/avatar'
        if not self.avatar_hash:
            self.generate_avatar_hash()
            db.session.add(self)
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=self.avatar_hash, size=size, default=default, rating=rating)

    def dump(self):
        schema = EmailAddressSchema()
        return schema.dump(self).data

    @property
    def fhir(self):
        """
        Returns fhir-client ContactPoint model object associated with SQLAlchemy Instance
        If no fhir-client object is initialized, one is created and stored in protected attrib _fhir
        :return:
            fhir-client ContactPoint object matching SQLAlchemy ORM object instance
        """
        if not getattr(self, '_fhir', None):
            self.create_fhir_object()
            return self._fhir
        else:
            return self._fhir

    @fhir.setter
    def fhir(self, fhir_obj):
        """
        Allows setting of the protected attribute _fhir
        Validates object is fhir-client model ContactPoint object
        :param fhir_obj:
            A fhir-client ContactPOint model object instance
        :return:
            None
        """
        if not isinstance(fhir_obj, contactpoint.ContactPoint):
            raise TypeError('Object is not a fhirclient ContactPoint object')
        else:
            self._fhir = fhir_obj

    def create_fhir_object(self):
        fhir_contact = contactpoint.ContactPoint()
        fhir_contact.system = 'email'
        if self.active:
            fhir_contact.use = 'home'
            if self.primary:
                fhir_contact.rank = 1
            else:
                fhir_contact.rank = 2
        else:
            fhir_contact.use = 'old'
            fhir_contact.rank = 3

        if self.email:
            fhir_contact.value = self.email

        self._fhir = fhir_contact

    def dump_fhir_json(self):
        self.create_fhir_object()
        return self.fhir.as_json()

    def generate_row_hash(self):
        data = {"email": self.email, "patient_id": self.patient_id, "user_id": self.user_id}
        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()
        if not self.avatar_hash:
            self.generate_avatar_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()
        if not self.avatar_hash:
            self.generate_avatar_hash()


##################################################################################################
# MARSHMALLOW SHCHEMA FOR EASY USER SERIALIZATION
##################################################################################################

class EmailAddressSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy EmailAddress model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    id = fields.Integer(attribute='id')
    email = fields.Email(attribute='email')
    primary = fields.Boolean(attribute='primary')
    active = fields.Boolean(attribute='active')
    patient_id = fields.Integer(attribute='patient_id')
    user_id = fields.Integer(attribute='user_id')
    gravatar_url = fields.String(attribute='gravatar_url', dump_only=True)
    created_at = fields.DateTime(attribute='created_at', dump_only=True)
    updated_at = fields.DateTime(attribute='updated_at', dump_only=True)
    row_hash = fields.String(attribute='row_hash', dump_only=True)

    @post_load
    def make_address(self, data):
        return EmailAddress(**data)


class EmailAddressAPI:
    def __init__(self, email=None, primary=False, active=True, patient_id=None, user_id=None):
        self.errors = {"critical": {},
                       "warning": {}}
        self._email_address = None

        self.email = email
        self.active = active
        self.primary = primary

        self.patient_id = patient_id
        self.user_id = user_id

    @property
    def email_address(self):
        if self._email_address:
            return self._email_address
        else:
            return None

    @email_address.setter
    def email_address(self, email_address):
        if email_address is None:
            pass
        elif isinstance(email_address, EmailAddress):
            self._email_address = email_address
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
            self.email = d.get('email', None)
            self.active = d.get('active', True)
            self.primary = d.get('primary', False)

            self.patient_id = d.get('patient_id', None)
            self.user_id = d.get('user_id', None)

    def validate_email(self):
        if self.email:
            try:
                self.email = validate_email(self.email)
            except ValueError as e:
                self.errors['critical']['email'] = e.args[0]
                self.email = None
        elif not self.email_address:
            self.errors['critical']['email'] = 'An email was not provided during email creation.  This is required.'

    def validate_active(self):
        if not isinstance(self.active, bool):
            self.active = None
            self.errors['warning']['active'] = 'The value provided for active was not a boolean.  Th default value' \
                                               ' will be used instead.'

    def validate_primary(self):
        if not isinstance(self.primary, bool):
            self.active = None
            self.errors['warning']['primary'] = 'The value provided for primary was not a boolean.  Th default value' \
                                                ' will be used instead.'

    def run_validations(self):
        self.validate_email()
        self.validate_active()
        self.validate_primary()

    def make_object(self):

        if self.errors['critical']:
            return None, self.errors

        else:
            if isinstance(self.email_address, EmailAddress):
                o = self.email_address
            else:
                o = EmailAddress()

            if self.email:
                o.email = self.email

            if self.user_id:
                o.user_id = self.user_id

            if self.patient_id:
                o.patient_id = self.patient_id

            if isinstance(self.active, bool):
                o.active = self.active

            if isinstance(self.primary, bool):
                o.primary = self.primary

            self.email_address = o

            return self.email_address, self.errors
