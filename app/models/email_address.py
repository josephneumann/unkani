from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.utils.general import json_serial
from app.models.extensions import BaseExtension

import hashlib, json


##################################################################################################
# SQL ALCHEMY EMAIL ADDRESS MODEL DEFINITION
##################################################################################################

class EmailAddress(sa.Model):
    __tablename__ = 'email_address'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    email = sa.Column("email", sa.Text, index=True)
    primary = sa.Column("primary", sa.Boolean, default=False)
    active = sa.Column("active", sa.Boolean, default=False)
    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'), index=True)
    patient = sa.relationship("Patient", back_populates="email_addresses")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), index=True)
    user = sa.relationship("User", back_populates="email_addresses")
    avatar_hash = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text, index=True)

    def __init__(self, email=None, primary=False, active=True):
        self.email = email
        self.primary = primary
        self.active = active

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
            sa.session.add(self)
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=self.avatar_hash, size=size, default=default, rating=rating)

    def dump(self):
        schema = EmailAddressSchema()
        return schema.dump(self).data

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

