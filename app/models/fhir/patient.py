from app import db, ma
from marshmallow import fields, post_load
from app.utils.demographics import *
from flask import url_for
from app.utils.general import json_serial
from app.models.fhir.address import Address, AddressSchema
from app.models.email_address import EmailAddress, EmailAddressSchema
from app.models.phone_number import PhoneNumber, PhoneNumberSchema
from app.models.extensions import BaseExtension
from fhirclient.models import patient as fhir_patient, meta, fhirdate, codeableconcept
from app.utils.fhir_utils import generate_humanname
import hashlib, json


class Patient(db.Model):
    __tablename__ = 'patient'
    __versioned__ = {}
    __mapper_args__ = {'extension': BaseExtension()}
    #TODO Add active boolean and add to FHIR generation

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text, index=True)
    last_name = db.Column(db.Text, index=True)
    middle_name = db.Column(db.Text)
    prefix = db.Column(db.Text)
    suffix = db.Column(db.Text)
    sex = db.Column(db.String)
    dob = db.Column(db.Date, index=True)
    ssn = db.Column(db.Text)
    race = db.Column(db.Text)
    ethnicity = db.Column(db.Text)
    marital_status = db.Column(db.String(3))
    deceased = db.Column(db.Boolean, default=False)
    deceased_date = db.Column(db.Date)
    multiple_birth = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)
    row_hash = db.Column(db.Text, index=True)
    addresses = db.relationship("Address", order_by=Address.id.desc(), back_populates="patient", lazy="dynamic",
                                cascade="all, delete, delete-orphan")
    email_addresses = db.relationship("EmailAddress", order_by=EmailAddress.id.desc(), back_populates="patient",
                                      lazy="dynamic",
                                      cascade="all, delete, delete-orphan")
    phone_numbers = db.relationship("PhoneNumber", order_by=PhoneNumber.id.desc(), back_populates="patient",
                                    lazy="dynamic",
                                    cascade="all, delete, delete-orphan")

    def __init__(self, first_name=None, last_name=None, middle_name=None, suffix=None, email=None,
                 home_phone=None, mobile_phone=None, work_phone=None, ssn=None, race=None, ethnicity=None, sex=None,
                 dob=None, deceased=False, deceased_date=None, addresses=None, multiple_birth=None,
                 preferred_language=None, **kwargs):
        if first_name:
            self.first_name = first_name
        if middle_name:
            self.middle_name = middle_name
        if last_name:
            self.last_name = last_name
        if suffix:
            self.suffix = suffix
        if ssn:
            self.ssn = ssn
        if race:
            self.race = race
        if ethnicity:
            self.ethnicity = ethnicity
        if sex:
            self.sex = sex
        if dob:
            self.dob = dob
        if deceased:
            self.deceased = deceased
        if deceased_date:
            self.deceased_date = deceased_date
        if multiple_birth:
            self.multiple_birth = multiple_birth
        if preferred_language:
            self.preferred_language = preferred_language

        phone_list = []

        if home_phone:
            home_phone = PhoneNumber(number=home_phone, type="HOME")
            if home_phone:
                phone_list.append(home_phone)

        if mobile_phone:
            mobile_phone = PhoneNumber(number=mobile_phone, type="MOBILE")
            if mobile_phone:
                phone_list.append(mobile_phone)

        if work_phone:
            work_phone = PhoneNumber(number=work_phone, type="WORK")
            if work_phone:
                phone_list.append(work_phone)

        if phone_list:
            for number in phone_list:
                self.phone_numbers.append(number)

        if email:
            n_email = None
            n_email = EmailAddress(email=email, active=True, primary=True)
            if n_email:
                self.email_addresses.append(n_email)

        if addresses:
            address_list = []
            for address in addresses:
                if isinstance(address, dict):
                    address1 = address.get("address1", None)
                    address2 = address.get("address2", None)
                    city = address.get("city", None)
                    state = address.get("state", None)
                    zipcode = address.get("zipcode", None)
                    primary = address.get("primary", True)
                    if not isinstance(primary, bool):
                        primary = True
                    address_list.append(Address(address1=address1, address2=address2, city=city, state=state,
                                                zipcode=zipcode, primary=primary))
            if address_list:
                primary_counter = 0
                for address in address_list:
                    if address.primary:
                        primary_counter += 1
                if primary_counter == 0:
                    address_list[0].primary = True
                if primary_counter > 1:
                    for address in address_list[1:]:
                        address.primary = False
                    address_list[0].primary = True
                for address in address_list:
                    self.addresses.append(address)

        self._fhir = None

    @property
    def primary_address(self):
        address_list = []
        address_list = self.addresses.all()
        primary = None
        if address_list:
            for address in address_list:
                if address.primary:
                    primary = address
            return primary
        else:
            return None

    @primary_address.setter
    def primary_address(self, address):
        if isinstance(address, dict):
            address1 = address.get("address1", None)
            address2 = address.get("address2", None)
            city = address.get("city", None)
            state = address.get("state", None)
            zipcode = address.get("zipcode", None)
            address = Address(address1=address1, address2=address2, city=city, state=state, zipcode=zipcode,
                              primary=True)

        else:
            address = address
            address_hash = address.generate_address_hash()
            current_addresses = self.addresses.all()
            match_address = None
            if current_addresses:
                for existing in current_addresses:
                    if existing.generate_address_hash() == address_hash:
                        match_address = existing
                        current_addresses.pop(current_addresses.index(existing))
                for current_addr in current_addresses:
                    if current_addr.primary:
                        current_addr.primary = False
                if match_address:
                    if not (match_address.primary and match_address.active):
                        match_address.primary = True
                        match_address.active = True
                else:
                    self.addresses.append(address)
            else:
                self.addresses.append(address)

    @property
    def home_phone(self):
        phone_list = self.phone_numbers
        if phone_list:
            home_phone = None
            for phone in phone_list:
                if phone.type == "HOME":
                    home_phone = phone
            if home_phone:
                return home_phone.number
            else:
                return None
        else:
            return None

    @property
    def mobile_phone(self):
        phone_list = self.phone_numbers
        if phone_list:
            mobile_phone = None
            for phone in phone_list:
                if phone.type == "MOBILE":
                    mobile_phone = phone
            if mobile_phone:
                return mobile_phone.number
            else:
                return None
        else:
            return None

    @property
    def work_phone(self):
        phone_list = self.phone_numbers
        if phone_list:
            work_phone = None
            for phone in phone_list:
                if phone.type == "WORK":
                    work_phone = phone
            if work_phone:
                return work_phone.number
            else:
                return None
        else:
            return None

    @property
    def email(self):
        email_list = self.email_addresses.all()
        primary_email = []
        if email_list:
            for email in email_list:
                if email.active and email.primary:
                    primary_email.append(email.email)
            if primary_email:
                return primary_email[0]

    @email.setter
    def email(self, email=None):
        if isinstance(email, str):
            email = EmailAddress(email=email, active=True, primary=True)
            if not email:
                raise ValueError("A valid email is required to create a user.")
            email_list = self.email_addresses.all()
            email_exists = False
            if email_list:
                for item in email_list:
                    if item.email == email.email:
                        item.active = True
                        item.primary = True
                        email_exists = True
                    else:
                        if item.active:
                            item.active = False
                        if item.primary:
                            item.primary = False
            if not email_exists:
                self.email_addresses.append(email)
        else:
            raise ValueError("A string value was not passed to the email parameter.  Unable to set email for user.")

    ####################################
    # RESOURCE URL BUILDER
    # ####################################
    def get_url(self):
        """
        Helper method to build the api url of the Patient resource
        :return:
            Returns the absolute URL of the Patient resource in the Patient api.
        """
        return url_for('api_v1.get_patient', id=self.id, _external=True)

    @property
    def fhir(self):
        """
        Returns fhir-client Patient model object associated with SQLAlchemy Instance
        If no fhir-client object is initialized, one is created and stored in protected attrib _fhir
        :return:
            fhir-client Patient object matching SQLAlchemy ORM object instance
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
        Validates object is fhir-client model Patient object
        :param fhir_obj:
            A fhir-client Patient model object instance
        :return:
            None
        """
        if not isinstance(fhir_obj, fhir_patient.Patient):
            raise TypeError('Object is not a fhirclient.models.address.Patient object')
        else:
            self._fhir = fhir_obj

    def create_fhir_object(self):
        fp = fhir_patient.Patient()

        # Set resource logical identifier
        fp.id = self.get_url()

        # Build and assign meta
        fm = meta.Meta()
        last_updated = fhirdate.FHIRDate()
        last_updated.date = self.updated_at
        fm.lastUpdated = last_updated
        fm.profile = ['http://hl7.org/fhir/StructureDefinition/Patient']
        # TODO: Included version id in meta
        fp.meta = fm

        fp.name = []
        fp.name.append(generate_humanname(use='official', first_name=self.first_name, last_name=self.last_name,
                                          middle_name=self.middle_name, suffix=self.suffix, prefix=self.prefix))

        fp.gender = self.sex

        fd_dob = fhirdate.FHIRDate()
        fd_dob.date = self.dob
        fp.birthDate = fd_dob

        fp.active = True

        self._fhir = fp

    def dump_fhir_json(self):
        self.create_fhir_object()
        return self.fhir.as_json()

    ##############################################################################################
    # Patient RANDOMIZATION UTILITIES
    ##############################################################################################
    def randomize_patient(self, demo_dict=None):
        __doc__ = """
        Patient Method: acts upon an initialized user object and randomizes key attributes
        of the user.

        Demo Dict:  Dictionary of demographic data supplied if needed.  Else, randomly created

        """
        if not isinstance(demo_dict, dict):
            demo_dict = list(random_demographics(number=1))[0]
            demo_dict = dict(demo_dict)
        self.first_name = demo_dict.get("first_name", None)
        self.last_name = demo_dict.get("last_name", None)
        self.middle_name = demo_dict.get("middle_name", None)
        self.suffix = demo_dict.get("suffix", None)
        self.dob = demo_dict.get("dob", None)
        self.email = demo_dict.get("email", None)
        self.sex = demo_dict.get("sex", None)
        self.ssn = demo_dict.get("ssn", None)
        self.race = demo_dict.get("race", None)
        self.ethnicity = demo_dict.get("ethnicity", None)
        self.marital_status = demo_dict.get("marital_status", None)
        self.deceased = demo_dict.get("deceased", False)
        self.preferred_language = random_language()

        addr = Address()
        addr.address1 = demo_dict.get("address1", None)
        addr.address2 = demo_dict.get("address2", None)
        addr.city = demo_dict.get("city", None)
        addr.state = demo_dict.get("state", None)
        addr.zipcode = demo_dict.get("zipcode", None)
        addr.active = True
        addr.primary = True
        addr.is_physical = True
        addr.is_postal = True
        addr.use = 'HOME'
        self.addresses.append(addr)

        phone_list = []
        home_phone = demo_dict.get("home_phone", None)
        mobile_phone = demo_dict.get("mobile_phone", None)
        work_phone = demo_dict.get("work_phone", None)

        if home_phone:
            home_phone = PhoneNumber(number=home_phone, type="HOME")
            if home_phone:
                phone_list.append(home_phone)

        if mobile_phone:
            mobile_phone = PhoneNumber(number=mobile_phone, type="MOBILE")
            if mobile_phone:
                phone_list.append(mobile_phone)

        if work_phone:
            work_phone = PhoneNumber(number=work_phone, type="WORK")
            if work_phone:
                phone_list.append(work_phone)

        if phone_list:
            prim_ph = random.choice(phone_list)
            prim_ph.primary = True
            for number in phone_list:
                self.phone_numbers.append(number)

    def generate_row_hash(self):
        data = {"first_name": self.first_name, "last_name": self.last_name, "middle_name": self.middle_name,
                "dob": self.dob, "sex": self.sex, "prefix": self.prefix, "suffix": self.suffix, "race": self.race,
                "ethnicity": self.ethnicity, "marital_status": self.marital_status, "deceased": self.deceased,
                "deceased_date": self.deceased_date, "multiple_birth": self.multiple_birth, "ssn": self.ssn,
                "preferred_language": self.preferred_language}

        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()


class PatientSchema(ma.Schema):
    """
    Marshmallow schema, associated with SQLAlchemy Patient model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""

    class Meta:
        exclude = ('addresses.patient_id', 'phone_numbers.patient_id', 'email_addresses.patient_id',
                   'addresses.user_id', 'phone_numbers.user_id', 'email_addresses.user_id')
        ordered = False

    id = fields.Integer(attribute="id", dump_only=True)
    first_name = fields.String(attribute="first_name")
    last_name = fields.String(attribute="last_name")
    middle_name = fields.String(attribute="middle_name")
    prefix = fields.String(attribute="prefix")
    suffix = fields.String(attribute="suffix")
    sex = fields.String(attribute='sex')
    dob = fields.Date(attribute='dob')
    ssn = fields.String(attribute='ssn')
    race = fields.String(attribute='race')
    ethnicity = fields.String(attribute='ethnicity')
    marital_status = fields.String(attribute='marital_status')
    addresses = fields.Nested(attribute='addresses', nested=AddressSchema, default=None, many=True)
    email_addresses = fields.Nested(attribute='email_addresses', nested=EmailAddressSchema, default=None, many=True)
    phone_numbers = fields.Nested(attribute='phone_numbers', nested=PhoneNumberSchema, default=None, many=True)
    deceased = fields.Boolean(attribute='deceased')
    deceased_date = fields.Date(attribute='deceased_date')
    multiple_birth = fields.Boolean(attribute='multiple_birth')
    preferred_language = fields.String(attribute='preferred_language')
    created_at = fields.DateTime(attribute='created_at')
    updated_at = fields.DateTime(attribute='updated_at')
    row_hash = fields.String(attribute='row_hash')

    @post_load
    def make_patient(self, data):
        return Patient(**data)


class PatientAPI:

    def __init__(self, first_name=None, last_name=None, middle_name=None, prefix=None, suffix=None, sex=None,
                 dob=None, ssn=None, race=None, ethnicity=None, marital_status=None, deceased=None,
                 deceased_date=None, multiple_birth=None, preferred_language=None, email=None, phone_numbers=None):
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.prefix = prefix
        self.suffix = suffix
        self.sex = sex
        self.dob = dob
        self.ssn = ssn
        self.race = race
        self.ethnicity = ethnicity
        self.marital_status = marital_status
        self.deceased = deceased
        self.deceased_date = deceased_date
        self.multiple_birth = multiple_birth
        self.preferred_language = preferred_language
        self.email = email
        self.phone_numbers = phone_numbers