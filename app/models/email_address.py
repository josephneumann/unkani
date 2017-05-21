from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.models.extensions import BaseExtension

import hashlib, json


class EmailAddress(sa.Model):
    __tablename__ = 'email_address'
    __mapper_args__ = {'extension': BaseExtension()}


    id = sa.Column(sa.Integer, primary_key=True, index=True)
    _email = sa.Column("email", sa.Text, unique=True, index=True)
    _primary = sa.Column("primary", sa.Boolean)
    _active = sa.Column("active", sa.Boolean, default=True)
    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'))
    patient = sa.relationship("Patient", back_populates="email_addresses")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    user = sa.relationship("User", back_populates="email_addresses")
    row_hash = sa.Column(sa.Text)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        email = normalize_email(email=email)
        if email:
            self._email = email

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
            self._primary = active

    def generate_row_hash(self):
        data = {"email": str(self.email), "active": str(self.active), "patient_id": str(self.patient_id),
                "user_id": str(self.user_id)}
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()
