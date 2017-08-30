from app.models.address import Address
from app.utils.demographics import *
import json


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
