from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.models.extensions import BaseExtension

import hashlib, json


class EmailAddress(sa.Model):
    __tablename__ = 'email_address'
    __mapper_args__ = {'extension': BaseExtension()}


    id = sa.Column(sa.Integer, primary_key=True, index=True)
    _email = sa.Column("email", sa.Text, index=True)
    _primary = sa.Column("primary", sa.Boolean, default=False)
    _active = sa.Column("active", sa.Boolean, default=False)
    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'), index=True)
    patient = sa.relationship("Patient", back_populates="email_addresses")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), index=True)
    user = sa.relationship("User", back_populates="email_addresses")
    avatar_hash = sa.Column(sa.Text)
    row_hash = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)

    def __init__(self, email=None, primary=False, active=False):
        self.email = email
        self.primary = primary
        self.active = active

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        if email:
            email = normalize_email(email=email)
            if email:
                self._email = email
            else:
                raise ValueError("A valid email must be provided to set the email attribute.")

    @property
    def primary(self):
        return self._primary

    @primary.setter
    def primary(self, primary):
        if isinstance(primary, bool):
            self._primary = primary

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        if isinstance(active, bool):
            self._active = active

    def generate_avatar_hash(self):
        __doc__ = """
        Generate an MD5 hash of the user's email.  Stores the result in the user
        'avatar_hash' attribute.  This value is used when constructing the gravatar URL."""
        if self.email and not re.search(r'(@EXAMPLE)+', self.email):
            email_lower = self.email.lower()
            self.avatar_hash = hashlib.md5(email_lower.encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
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

    def generate_row_hash(self):
        data = {"email": self.email, "patient_id": self.patient_id, "user_id": self.user_id}
        for key in data:
            data[key] = str(data[key])
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()
