from app.models.email_address import EmailAddress
from app.utils.demographics import *
import json


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
