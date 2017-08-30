from flask import request, jsonify, g, url_for

import json
from app import sa
from app.security import *
from . import api
from .authentication import token_auth
from .errors import *
from app.models.phone_number import PhoneNumber
from app.utils.demographics import *


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
