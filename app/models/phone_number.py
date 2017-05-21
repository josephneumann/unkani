from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.models.extensions import BaseExtension
import hashlib, json


class PhoneNumber(sa.Model):
    __tablename__ = 'phone_number'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True)
    _number = sa.Column("number", sa.Text, nullable=False)
    _type = sa.Column("type", sa.String(1), nullable=False)
    active = sa.Column(sa.Boolean, default=True)
    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'))
    patient = sa.relationship("Patient", back_populates="phone_numbers")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    user = sa.relationship("User", back_populates="phone_numbers")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text)

    def __init__(self, number=None, type=None, active=True, **kwargs):
        if not number and type:
            raise ValueError("Both a phone number and type are required to create phone number.")
        if not isinstance(active, bool):
            raise TypeError("The active parameter was not set to a boolean value.")
        else:
            number = normalize_phone(phone=number)
            if number:
                self._number = number
                self.type = type
                self.active = active
            else:
                raise ValueError("Invalid phone number provided.")

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, phone_dict):
        required_keys = ["number"]
        optional_keys = ["type", "active"]
        if isinstance(phone_dict, dict):
            number = phone_dict.get("number", None)
            type = phone_dict.get("type", self.type)
            active = phone_dict.get("active", self.active)
            if not isinstance(active, bool):
                active = self.active
            if not number:
                raise ValueError(
                    "A dictionary with the required keys {} was not provided to this setter method.".format(
                        required_keys))
            else:
                number = normalize_phone(phone=number)
                if not number:
                    raise ValueError("A valid phone number was not provided.")
                else:
                    self._number = number
                    self.type = type
                    self.active = active
                    self.updated_at = datetime.utcnow()
        else:
            raise TypeError(
                "A dictionary must be supplied to this setter method, with the following required keys:\
                 {} and the following optional keys: {}.".format(
                    required_keys, optional_keys))

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type=None):
        type_dict = {"H": frozenset(["H", "HOME", "HOME PHONE", "HOUSE", "HOUSE PHONE", "LAND LINE"]),
                     "C": frozenset(["C", "CELL", "MOBILE", "M", "CELL PHONE", "MOBILE PHONE"]),
                     "W": frozenset(["W", "WORK", "WORK PHONE", "B", "BUSINESS", "BUSINESS PHONE"])}
        if not type:
            raise ValueError(
                "No phone number type provided. A value in the allowed dictionary must be provided: {}".format(
                    type_dict))
        type = str(type).upper().strip()
        n_type = None
        for key in type_dict:
            if type in type_dict[key]:
                n_type = key
        if not n_type:
            raise ValueError("Phone number type was not in the allowed dictionary of values {}".format(type_dict))
        else:
            if self._sa_instance_state.persistent:
                self.updated_at = datetime.utcnow()
            self._type = n_type

    def generate_row_hash(self):
        data = {"number": str(self.number), "type": str(self.type), "patient_id": str(self.patient_id),
                "user_id": str(self.user_id), "active": str(self.active)}
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()
