from app import db, ma
from marshmallow import fields, post_load
import hashlib, json

from app.utils.demographics import *
from app.utils.general import json_serial
from app.models.extensions import BaseExtension
from fhirclient.models import address as fhir_address
from fhirclient.models import period, fhirdate
from fhirclient.models.fhirabstractbase import FHIRValidationError


class Address(db.Model):
    """
    SQL Alchemy Address object model definition
    ORM object that mediates create, modify and delete operations on the address database table
    A variety of normalizaton and validation methods are defined
    Methods for (de)serializing objects are also defined
    """
    # TODO: Add county and country to model, api and FHIR output
    _tablename__ = 'address'
    __versioned__ = {}
    __mapper_args__ = {'extension': BaseExtension()}
    id = db.Column(db.Integer, primary_key=True)
    address1 = db.Column("address1", db.Text)
    address2 = db.Column("address2", db.Text)
    city = db.Column("city", db.Text)
    state = db.Column("state", db.String(2))
    zipcode = db.Column("zipcode", db.Text, index=True)
    primary = db.Column("primary", db.Boolean)
    active = db.Column("active", db.Boolean, default=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), index=True)
    patient = db.relationship("Patient", back_populates="addresses")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    user = db.relationship("User", back_populates="addresses")
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)
    address_hash = db.Column(db.Text)
    row_hash = db.Column(db.Text)
    start_date = db.Column("start_date", db.Date, default=date.today())
    end_date = db.Column("end_date", db.Date)
    is_postal = db.Column("is_postal", db.Boolean, default=True)
    is_physical = db.Column("is_physical", db.Boolean, default=True)
    use = db.Column("use", db.Text)

    def __init__(self, address1=None, address2=None, city=None, state=None, zipcode=None, active=True, primary=False,
                 user_id=None, patient_id=None, start_date=None, end_date=None, is_postal=True, is_physical=True,
                 use=None, **kwargs):
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.active = active
        self.primary = primary
        self.user_id = user_id
        self.patient_id = patient_id
        self.start_date = start_date
        self.end_date = end_date
        self.is_postal = is_postal
        self.is_physical = is_physical
        self.use = use

        self._fhir = None

    @property
    def fhir(self):
        """
        Returns fhir-client Address model object associated with SQLAlchemy Instance
        If no fhir-client object is initialized, one is created and stored in protected attrib _fhir
        :return:
            fhir-client Address object matching SQLAlchemy ORM object instance
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
        Validates object is fhir-client model Address object
        :param fhir_obj:
            A fhir-client Address model object instance
        :return:
            None
        """
        if not isinstance(fhir_obj, fhir_address.Address):
            raise TypeError('Object is not a fhirclient.models.address.Address object')
        else:
            self._fhir = fhir_obj

    def formatted_address(self):
        """
        Method to return a formatted address string

        :return:
            A formatted address string with the multi-line format
            Address1
            Address2
            City, State Zipcode
        """
        address_text = "{}{}{}{}{}".format(self.address1 + '\n' if self.address1 else '',
                                           self.address2 + '\n' if self.address2 else ''
                                           , self.city + ', ' if self.city else ''
                                           , self.state + ' ' if self.state else ' '
                                           , self.zipcode if self.zipcode else '')
        return address_text

    def dump(self):
        """
        Method to quickly dump the Address object via Marshmallow schema
        :return:
            JSON string of object serialized with Marshmallow default schema
        """
        schema = AddressSchema()
        return schema.dump(self).data

    def create_fhir_object(self):
        """
        method: create_fhir_object()
        Create a fhir-client.model.address.Adress object and stores to the self.fhir attribute

        :return:
            None
        """
        # Initialize FHIRclient Address object
        # Assign Address object attributes to FHIRclient Address object
        fa = fhir_address.Address()

        if self.address1:
            fa.line = [self.address1]

            if self.address2:
                fa.line.append(self.address2)

        if self.city:
            fa.city = self.city

        if self.state:
            fa.state = self.state

        if self.zipcode:
            fa.postalCode = self.zipcode

        fa.text = self.formatted_address()

        if isinstance(self.start_date, date) or isinstance(self.end_date, date):
            p = period.Period()

            if self.start_date:
                fhirdate_start = fhirdate.FHIRDate()
                fhirdate_start.date = self.start_date
                p.start = fhirdate_start

            if self.end_date:
                fhirdate_end = fhirdate.FHIRDate()
                fhirdate_end.date = self.end_date
                p.end = fhirdate_end

            fa.period = p

        if self.use:
            fa.use = self.use.lower()

        if self.is_postal and self.is_physical:
            fa.type = 'both'

        elif self.is_postal:
            fa.type = 'postal'

        elif self.is_physical:
            fa.type = 'physical'

        self.fhir = fa

    def dump_fhir_json(self, parent=False):
        """
        Method to dump valid FHIR STU 3.0 JSON representation of the Address ORM object

        :param parent:
            When True, outputs JSON with resourceType key and relevant meta-data populated
            When False, ignores these attributes in JSON construction
        :return:
            FHIR STU 3.0 Address JSON matching ORM Address Object
        """
        self.create_fhir_object()
        try:
            fhir_json = self.fhir.as_json()
            if parent:
                fhir_json['resourceType'] = self.fhir.resource_type
                # TODO: Add meta and identity items to serialize here
            return fhir_json

        except FHIRValidationError:
            return None

    def generate_row_hash(self):
        """
        Method to generate a sha1 hash of the object attributes.  Used for versioning and cache control
        :return:
            A SHA-1 hash of JSON object containing an ordered dictionary of the Address object's attributes
        """
        data = {"address1": self.address1, "address2": self.address2, "city": self.city,
                "state": self.state, "zipcode": self.zipcode,
                "patient_id": self.patient_id, "user_id": self.user_id, "is_postal": self.is_postal,
                "is_physical": self.is_physical, "use": self.use, "start_date": self.start_date,
                "end_date": self.end_date}
        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def generate_address_hash(self):
        """
        Method to generate a sha1 hash of the object attributes that uniquely identify an address (less the additional
        address meta data).  Used to check for matching addresses.
        :return:
            A SHA-1 hash of a normalized Address object's attributes that uniquely define the address. These include
            the address lines, city, state and zipcodes.  The data are normalized into an ordered dict that takes care
            to remove whitespaces and other noise from the attribute values.  The ordered dict of values is serialized
            as a JSON string and a SHA-1 hash is created from the JSON serialization.

        """
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
        """
        Method to run operations before object is inserted into database table
        :return:
            No return
        """
        self.row_hash = self.generate_row_hash()
        self.address_hash = self.generate_address_hash()

    def before_update(self):
        """
        Method to run operations before object's record in the database table is updated
        :return:
            No return
        """
        self.row_hash = self.generate_row_hash()
        self.address_hash = self.generate_address_hash()


class AddressSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy Address model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input.
    
    Notice:  This is separate from the FHIR STU 3.0 serialization and de-serialization methods
    """
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
    start_date = fields.Date(attribute='start_date')
    end_date = fields.Date(attribute='end_date')
    is_postal = fields.Boolean(attribute='is_postal')
    is_physical = fields.Boolean(attribute='is_physical')
    use = fields.String(attribute='use')
    created_at = fields.DateTime(attribute='created_at')
    updated_at = fields.DateTime(attribute='updated_at')
    address_hash = fields.String(attribute='address_hash')
    row_hash = fields.String(attribute='row_hash')

    @post_load
    def make_address(self, data):
        return Address(**data)


class AddressAPI:
    """
    AddressAPI:  An object class that mediates all operations on Address objects.  May be used in
    conjunction with as REST API or within view functions of the Flask App.

    Core Uses:
        1) De-serialize JSON representations of Addresses to SQLAlchemy.orm Address model objects.
        2) Apply normalization and validation logic to Address attributes
        3) Update existing or create new SQLAlchemy.orm Address model objects with normalized
            and validated data.

    Example Usage With Existing Address Object:

        existing_address = Address.query.get_or_404(<someaddressid>)

        api = AddressAPI()
        api.address = existing_address

        api.city = 'Madison'
        api.state = 'WI'

        api.run_validations()
        if not api.errors['critical']:
            updated_address, errors = api.make_object()

            if updated_address:
                sa.session.add(updated_address)

    An Address resource is not typically operated upon directly by a REST API.  Instead, the AddressAPI class is
    used in conjuction with person or non-person resources associated with the address.  The address is manipulated
    via that object instead

    """

    def __init__(self, address1=None, address2=None, city=None, state=None, zipcode=None, primary=False, active=True,
                 patient_id=None, user_id=None, start_date=None, end_date=None, is_postal=None, is_physical=None,
                 use=None):
        self.errors = {"critical": {},
                       "warning": {}}
        self._address = None
        self._validation_passed = False

        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.active = active
        self.primary = primary
        self.start_date = start_date
        self.end_date = end_date
        self.is_postal = is_postal
        self.is_physical = is_physical
        self.use = use

        self.patient_id = patient_id
        self.user_id = user_id

    @property
    def address(self):
        """
        Method to access protected self._address attribute

        :return:
            If a SQLAlchemy Address type object is assigned to self._address, returns that object
            Else None
        """
        if self._address:
            return self._address
        else:
            return None

    @address.setter
    def address(self, address):
        """
        Setter method for full address
        Allows assigning a SQLAlchemy Address model object to the protected attribute self._address
        Used to store an existing SQLAlchemy address model object in the API validation utility
        :param address:
            Must be a SQLAlchemy Address model object
        :return:
            None or TypeError if inappropriate object is assigned
        """
        if address is None:
            pass
        elif isinstance(address, Address):
            self._address = address
        else:
            raise TypeError('Object assigned to user was not a SQL Alchemy Address type object.')

    def loads_json(self, data):
        """
        Used to load JSON formatted address data, or native python dict object.  Parses all data from the
        source and stores in class instance's corresponding attributes.  These attributes are validated, normalized
        and ultimately dumped with other methods such as: self.run_validations() and self.make_object()

        :param data:
            type:
                JSON encoded string with valid Address object key-value pairs.
                OR
                Native python dict with valid Address object key-value pairs
        :return:
            Nothing
        """
        d = None
        if isinstance(data, dict):  # Handle native python dicts
            d = data
        else:
            try:
                d = json.loads(data)  # Try loading JSON encoded string
            except json.decoder.JSONDecodeError as e:  # Handle JSON decode error.  Store in error dict
                self.errors['critical'][
                    'json decode error'] = 'An error occurred when attempting to decode JSON: {}'.format(e.args[0])

        if d:
            self.address1 = d.get('address1', None)
            self.address2 = d.get('address2', None)
            self.city = d.get('city', None)
            self.state = d.get('state', None)
            self.zipcode = d.get('zipcode', None)
            self.primary = d.get('primary', False)
            self.active = d.get('active', True)
            self.start_date = d.get('start_date', None)
            self.end_date = d.get('end_date', None)
            self.is_postal = d.get('is_postal', None)
            self.is_physical = d.get('is_physical', None)
            self.use = d.get('use', None)

            self.patient_id = d.get('patient_id', None)
            self.user_id = d.get('user_id', None)

    def validate_address(self):
        """
        Validation method for address components
        Normalizes the values assigned to address1, address2, city, state and zipcode
        If a value cannot be normalized, the attribute is set to null and a warning is logged in the error array
        :return:
            None
        """
        from app.utils import normalize_address
        addr_dict = normalize_address(address1=self.address1, address2=self.address2,
                                      city=self.city, state=self.state, zipcode=self.zipcode)

        self.address1 = addr_dict.get('address1', None)
        self.address2 = addr_dict.get('address2', None)

        if self.city:
            if not addr_dict.get('city', None):
                self.errors['warning'][
                    'city'] = 'The value {} could not be normalized and assigned to the city attribute.'.format(
                    str(self.city))
            else:
                self.city = addr_dict.get('city', None)

        if self.state:
            if not addr_dict.get('state', None):
                self.errors['warning'][
                    'state'] = 'The value {} could not be normalized and assigned to the state attribute.'.format(
                    str(self.state))
            else:
                self.state = addr_dict.get('state', None)

        if self.zipcode:
            if not addr_dict.get('zipcode', None):
                self.errors['warning'][
                    'zipcode'] = 'The value {} could not be normalized and assigned to the zipcode attribute.'.format(
                    str(self.zipcode))
            else:
                self.zipcode = addr_dict.get('zipcode', None)

    def validate_active(self):
        """
        Validation method for self.active
        Ensures a boolean is assigned to address.active
        Logs warning in error array if non null and non bool type value is assigned
        :return:
            None
        """
        if not isinstance(self.active, bool):
            self.active = None

    def validate_primary(self):
        """
        Validation method for self.primary
        Ensures a boolean is assigned to address.primary
        Logs warning in error array if non null and non bool type value is assigned
        :return:
            None
        """
        if not isinstance(self.primary, bool):
            self.active = None

    def validate_type(self):
        """
        Validation method for is_physical and is_postal
        Ensures that if neither address options are true, they are set to be both True
        Since no address can neither be postal or physical in the system
        :return:
        """
        if not (self.is_physical or self.is_physical):
            self.is_postal = True
            self.is_physical = True

    def validate_use(self):
        """
        Validation method for self.use
        Ensures self.use value conforms to FHIR STU3 Address.use constraints
        :return:
        """
        if self.use:
            if not isinstance(self.use, str):
                self.use = None
            use = str(self.use).strip().upper()
            n_use = None
            use_dict = {"HOME": {"H", "HOUSE", "PERSONAL"},
                        "WORK": {"W", "BUSINESS", "JOB"},
                        "TEMP": {"T", "TEMPORARY"},
                        "OLD": {"O", "FORMER", "PAST", "PREVIOUS", "PREV"},
                        }
            if use in use_dict:
                n_use = use

            for key in use_dict:
                if use in use_dict[key]:
                    n_use = key

            if n_use:
                self.use = n_use

            else:
                self.use = None

    def validate_start_date(self):
        """
        Validation method for self.start_date
        Uses dateutils datetime parser to handle any format of dates.
        :return:
            If self.start_date exists and can be validated as a date, sets self.start_date as a datetime.date  object
            If self.start_date cannot be parsed into a valid date, sets self.start_date to None & logs a critical error
                under the key 'start_date' with detailed information about the error.
        """
        if self.start_date:
            try:
                self.start_date = validate_dob(self.start_date)
            except ValueError as e:
                self.errors['warning']['start_date'] = e.args[0]
                self.start_date = None

    def validate_is_postal(self):
        """
        Validation method for self.is_postal
        Ensures a boolean is assigned to address.is_postal
        Logs warning in error array if non null and non bool type value is assigned
        :return:
            None
        """
        if not isinstance(self.is_postal, bool):
            self.is_postal = None
            self.errors['warning']['is_postal'] = 'A non-boolean type value was assigned to address.is_postal'

    def validate_is_physical(self):
        """
        Validation method for self.is_physical
        Ensures a boolean is assigned to address.is_physical
        Logs warning in error array if non null and non bool type value is assigned
        :return:
            None
        """
        if not isinstance(self.is_physical, bool):
            self.is_physical = None
            self.errors['warning']['is_physical'] = 'A non-boolean type value was assigned to address.is_physical'

    def validate_end_date(self):
        """
        Validation method for self.end_date
        Uses dateutil's datetime parser to handle any format of dates.
        :return:
            If self.end_date exists and can be validated as a date, sets self.end_date as a datetime.date  object
            If self.end_date cannot be parsed into a valid date, sets self.end_date to None & logs a critical error
                under the key 'end_date' with detailed information about the error.
        """
        if self.end_date:
            try:
                self.end_date = validate_dob(self.end_date)
            except ValueError as e:
                self.errors['warning']['end_date'] = e.args[0]
                self.end_date = None

    def validate_date_range(self):
        """
        Validation method for start and end date
        Ensures start_date, if not null, is a date on or before the end_date
        Logs warning in error array if start and end date values are out of sequence
        :return:
            None
        """
        if self.start_date and self.end_date:
            if not self.start_date <= self.end_date:
                self.start_date = None
                self.end_date = None
                self.errors['warning']['date_range'] = 'Invalid date range: End date was not after the start date.'

    def run_validations(self):
        """
        Method to run all individual validation methods
        Each method normalizes values and logs errors as necessary
        :return:
            None
        """
        self.validate_address()
        self.validate_active()
        self.validate_primary()
        self.validate_type()
        self.validate_use()
        self.validate_start_date()
        self.validate_end_date()
        self.validate_date_range()
        self.validate_is_physical()
        self.validate_is_postal()

        if not self.errors['critical']:
            self._validation_passed = True
        else:
            self._validation_passed = False

    def make_object(self):
        """
        Method to process post-validated AddressAPI object.
        Requires self.run_validations() to be called before running.
        :return:
            If self.run_validations() has not been completed, returns the tuple (None, self.errors)
            If critical errors are logged, returns the tuple (None, self.errors)
            If validations passed and an existing address is logged to self.address, returns the tuple
            (address, self.errors) where address is the existing and now updated address object and self.errors
            is the error dictionary.
            If no address exists and is assigned to self.address, creates a new address object and returns it in
            the tuple (address, errors)

        """
        if not self._validation_passed:
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

            if self.start_date:
                a.start_date = self.start_date

            if self.end_date:
                a.end_date = self.end_date

            if isinstance(self.is_postal, bool):
                a.is_postal = self.is_postal

            if isinstance(self.is_physical, bool):
                a.is_physical = self.is_physical

            if self.use:
                a.use = self.use

            self.address = a

            return self.address, self.errors
