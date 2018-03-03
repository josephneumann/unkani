from app import db, ma
from sqlalchemy.dialects.postgresql import UUID as postgresql_uuid
from marshmallow import fields, post_load
from app.utils.demographics import *
from flask import url_for, render_template
from app.utils.general import json_serial
from app.models.fhir.address import Address, AddressSchema
from app.models.fhir.email_address import EmailAddress, EmailAddressSchema
from app.models.fhir.phone_number import PhoneNumber, PhoneNumberSchema
from app.models.fhir.codesets import ValueSet, CodeSystem
from app.models.extensions import BaseExtension
from fhirclient.models import patient as fhir_patient, meta, codeableconcept, coding, extension, identifier, narrative
from app.utils.fhir_utils import fhir_gen_humanname, fhir_gen_datetime
from app.utils.demographics import race_dict, ethnicity_dict
import hashlib, json, uuid


class Patient(db.Model):
    __tablename__ = 'patient'
    __versioned__ = {}
    __mapper_args__ = {'extension': BaseExtension()}

    id = db.Column(db.Integer, primary_key=True, index=True)
    uuid = db.Column(postgresql_uuid(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
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
    active = db.Column(db.Boolean, default=True, nullable=False)
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
                 preferred_language=None, active=None, **kwargs):
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

        if isinstance(active, bool):
            self.active = active

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

    @property
    def dob_string(self):
        __doc__ = """
        Represent Patient's DOB as a string with format 'YYYY-MM-DD'
        """
        if self.dob:
            return self.dob.strftime('%Y-%m-%d')
        else:
            return None

    ####################################
    # RESOURCE URL BUILDER
    # ####################################
    def get_url(self):
        """
        Helper method to build the api url of the Patient resource
        :return:
            Returns the absolute URL of the Patient resource in the Patient api.
        """
        return url_for('api_v1.patient_read', id=self.id, _external=True)

    ############################################
    # VERSIONING UTILITY PROPERTIES AND METHODS
    ############################################
    @property
    def version_number(self):
        if self.versions:
            return len(self.versions.all())
        raise ValueError('No versions exist for this object.')

    def latest_version(self):
        if self.versions:
            return self.versions[len(self.versions.all()) - 1]
        raise ValueError('No versions exist for this object.')

    def previous_version(self):
        try:
            lv = self.latest_version()
            return lv.previous
        except:
            raise ValueError('No versions exist for this object.')

    def first_version(self):
        if self.versions:
            return self.versions[0]
        raise ValueError('No versions exist for this object.')

    @property
    def previous_version_url(self):
        return None
        # TODO: Implement URL builder when API route exists
        # if self.versions and self.version_number > 1:
        #     return url_for('api_v1.get_user_version', userid=self.id, version_number=self.version_number - 1,
        #                    _external=True)
        # else:
        #     return None

    ############################################
    # FHIR STU 3 UTILITY PROPERTIES AND METHODS
    ############################################

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
        """
        Generate a fhirclient.Patient class object and store in the protected attribute _fhir
        :return:
            None
        """
        # Initialize Patient resource
        fhir_pt = fhir_patient.Patient()

        # Set resource logical identifier
        fhir_pt.id = self.get_url()

        # Build and assign Meta resource for Patient object
        fhir_meta = meta.Meta()
        fhir_meta.lastUpdated = fhir_gen_datetime(value=self.updated_at, error_out=False, to_date=False)
        fhir_meta.versionId = str(self.version_number)
        fhir_meta.profile = ['http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient']
        fhir_pt.meta = fhir_meta

        # Patient name represented as HumanName resource
        fhir_pt.name = []
        fhir_pt.name.append(fhir_gen_humanname(use='usual', first_name=self.first_name, last_name=self.last_name,
                                               middle_name=self.middle_name, suffix=self.suffix, prefix=self.prefix))
        # Display MRN as identifier codeable concept = Patient.identifier.codeableconcept.coding
        # Initialize Identifier resource
        id_mrn = identifier.Identifier()
        id_mrn.use = 'usual'
        id_mrn.system = 'http://unkani.com'
        id_mrn.value = str(self.uuid)

        # Initialize CodeableConcept resource
        mrn_cc = codeableconcept.CodeableConcept()
        mrn_cc.text = 'Medical Record Number'

        # Initialize Coding resource
        mrn_coding = coding.Coding()
        mrn_coding.system = 'http://hl7.org/fhir/v2/0203'
        mrn_coding.code = 'MR'
        mrn_coding.display = 'Medical Record Number'

        # Assign Coding resource to CodeableConcept
        mrn_cc.coding = [mrn_coding]

        # Assign CodeableConcept to Identifier
        id_mrn.type = mrn_cc

        # Assign CodeableConcept to Patient
        fhir_pt.identifier = [id_mrn]

        # Display SSN as identifier codeable concept = Patient.identifier.codeableconcept.coding
        if self.ssn:
            # Initialize Identifier resource
            id_ssn = identifier.Identifier()
            id_ssn.use = 'usual'
            id_ssn.system = 'http://hl7.org/fhir/sid/us-ssn'
            id_ssn.value = self.ssn

            # Initialize CodeableConcept resource
            ssn_cc = codeableconcept.CodeableConcept()
            ssn_cc.text = 'Social Security Number'

            # Initialize Coding resource
            ssn_coding = coding.Coding()
            ssn_coding.system = 'http://hl7.org/fhir/v2/0203'
            ssn_coding.code = 'SS'
            ssn_coding.display = 'Social Security Number'

            # Assign Coding resource to CodeableConcept
            ssn_cc.coding = [ssn_coding]

            # Assign CodeableConcept to Identifier
            id_ssn.type = ssn_cc

            # Assign CodeableConcept to Patient
            fhir_pt.identifier.append(id_ssn)

        if self.marital_status:
            marital_status_cc = codeableconcept.CodeableConcept()
            marital_status_url = 'http://hl7.org/fhir/ValueSet/marital-status'
            marital_status_concept = ValueSet.get_valueset_concept(marital_status_url, self.marital_status)
            if marital_status_concept:
                marital_status_cc.text = getattr(marital_status_concept, 'display')
            marital_status_coding = coding.Coding()
            marital_status_coding.code = self.marital_status
            marital_status_coding.system = marital_status_url
            marital_status_coding.display = marital_status_cc.text

            marital_status_cc.coding = [marital_status_coding]
            fhir_pt.maritalStatus = marital_status_cc

        if self.race:
            ext_race = extension.Extension()
            ext_race.url = 'http://hl7.org/fhir/StructureDefinition/us-core-race'
            race_url = 'http://hl7.org/fhir/us/core/ValueSet/omb-race-category'
            cc_race = codeableconcept.CodeableConcept()
            race_concept = ValueSet.get_valueset_concept(race_url, self.race)
            if race_concept:
                cc_race.text = getattr(race_concept, 'display')
            coding_race = coding.Coding()
            coding_race.system = race_url
            coding_race.code = self.race
            coding_race.display = cc_race.text
            cc_race.coding = [coding_race]
            ext_race.valueCodeableConcept = cc_race
            try:
                fhir_pt.extension.append(ext_race)
            except AttributeError:
                fhir_pt.extension = [ext_race]

        if self.ethnicity:
            ext_ethnicity = extension.Extension()
            ext_ethnicity.url = 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity'
            cc_ethnicity = codeableconcept.CodeableConcept()
            cc_ethnicity.text = ethnicity_dict.get(self.ethnicity)[0].capitalize()
            coding_ethnicity = coding.Coding()
            coding_ethnicity.system = 'http://hl7.org/fhir/us/core/ValueSet/omb-ethnicity-category'
            coding_ethnicity.code = self.race
            coding_ethnicity.display = cc_ethnicity.text
            cc_ethnicity.coding = [coding_ethnicity]
            ext_ethnicity.valueCodeableConcept = cc_ethnicity

            try:
                fhir_pt.extension.append(ext_ethnicity)
            except AttributeError:
                fhir_pt.extension = [ext_ethnicity]

        if self.sex:
            sex_dict = {"administrativeGender": {"M": "male", "F": "female", "u": "unknown", "o": "other"},
                        "usCoreBirthSex": {"M": "M", "F": "F", "U": "UNK", "O": "UNK"}}

            fhir_pt.gender = sex_dict['administrativeGender'][str(self.sex).upper()]

            ext_birth_sex = extension.Extension()
            ext_birth_sex.url = 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex'
            ext_birth_sex.valueCode = sex_dict['usCoreBirthSex'][str(self.sex).upper()]

            try:
                fhir_pt.extension.append(ext_birth_sex)
            except AttributeError:
                fhir_pt.extension = [ext_birth_sex]

        if self.dob:
            fhir_pt.birthDate = fhir_gen_datetime(value=self.dob, to_date=True)

        fhir_pt.active = self.active

        fhir_pt.deceasedBoolean = self.deceased

        if self.deceased_date:
            fhir_pt.deceasedDateTime = fhir_gen_datetime(value=self.deceased_date, to_date=False)

        if self.preferred_language:
            fhir_comm = fhir_patient.PatientCommunication()
            fhir_comm.preferred = True
            fhir_lang_cc = codeableconcept.CodeableConcept()
            fhir_lang_coding = coding.Coding()
            fhir_lang_coding.code = self.preferred_language
            fhir_lang_url = 'http://hl7.org/fhir/ValueSet/languages'
            fhir_lang_coding.system = fhir_lang_url
            fhir_lang_concept = ValueSet.get_valueset_concept(fhir_lang_url, self.preferred_language)
            if fhir_lang_concept:
                fhir_lang_coding.display = fhir_lang_concept.display
                fhir_lang_cc.text = fhir_lang_coding.display
            fhir_lang_cc.coding = [fhir_lang_coding]
            fhir_comm.language = fhir_lang_cc
            fhir_pt.communication = [fhir_comm]

        contact_point_list = []

        phone_list = self.phone_numbers.all()
        if phone_list:
            for ph in phone_list:
                contact_point_list.append(ph.fhir)

        email_list = self.email_addresses.all()
        if email_list:
            for em in email_list:
                contact_point_list.append(em.fhir)

        if contact_point_list:
            fhir_pt.telecom = contact_point_list

        address_list = self.addresses.all()
        if address_list:
            fhir_pt.address = []
            for addr in address_list:
                fhir_pt.address.append(addr.fhir)

        xhtml = render_template('fhir/patient.html', fhir_patient=fhir_pt, patient=self)
        fhir_pt.text = narrative.Narrative()
        fhir_pt.text.status = 'generated'
        fhir_pt.text.div = xhtml

        self._fhir = fhir_pt

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
        self.deceased_date = demo_dict.get("deceased_date", None)
        self.preferred_language = demo_dict.get("preferred_language", None)
        self.multiple_birth = demo_dict.get("multiple_birth", False)

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
                "preferred_language": self.preferred_language, "active": self.active}

        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        """
        Stuff to do before record is inserted into database
        :return: None
        """
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        """
        Stuff to do before record is updated in database
        :return: None
        """
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
    active = fields.Boolean(attribute='active')
    created_at = fields.DateTime(attribute='created_at')
    updated_at = fields.DateTime(attribute='updated_at')
    row_hash = fields.String(attribute='row_hash')

    @post_load
    def make_patient(self, data):
        return Patient(**data)


class PatientAPI:

    def __init__(self, first_name=None, last_name=None, middle_name=None, prefix=None, suffix=None, sex=None,
                 dob=None, ssn=None, race=None, ethnicity=None, marital_status=None, deceased=None,
                 deceased_date=None, multiple_birth=None, preferred_language=None, email=None, phone_numbers=None,
                 active=None):
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
        self.active = active
