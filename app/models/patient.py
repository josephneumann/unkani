from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.models import Address, EmailAddress, PhoneNumber
from app.models.extensions import BaseExtension


class Patient(sa.Model):
    __tablename__ = 'patient'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True)
    _first_name = sa.Column("first_name", sa.Text)
    _last_name = sa.Column("last_name", sa.Text)
    _middle_name = sa.Column("middle_name", sa.Text)
    _suffix = sa.Column("suffix", sa.Text)
    _sex = sa.Column("sex", sa.String(1))
    _dob = sa.Column("dob", sa.Date)
    _ssn = sa.Column("ssn", sa.Text)
    _race = sa.column("race", sa.Text)
    _ethnicity = sa.column("ethnicity", sa.Text)
    _marital_status = sa.column("marital_status", sa.String(1))
    email_addresses = sa.relationship("EmailAddress", back_populates="patient", cascade="all, delete, delete-orphan")
    _deceased = sa.Column("deceased", sa.Boolean)
    addresses = sa.relationship("Address", order_by=Address.id.desc(), back_populates="patient", lazy="dynamic",
                                cascade="all, delete, delete-orphan")
    phone_numbers = sa.relationship("PhoneNumber", order_by=PhoneNumber.id.desc(), back_populates="patient", lazy="dynamic",
                                cascade="all, delete, delete-orphan")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text)

    def __init__(self, first_name=None, last_name=None, middle_name=None, suffix=None, email=None,
                 home_phone=None, cell_phone=None, work_phone=None, ssn=None, race=None, ethnicity=None, sex=None,
                 dob=None, deceased=False, addresses=None, **kwargs):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name, self.suffix = normalize_lastname_suffix(last_name=last_name, suffix=suffix)
        self.ssn = ssn
        self.race = race
        self.ethnicity = ethnicity
        self.sex = sex
        self.dob = dob
        self.deceased = deceased

        home_phone = normalize_phone(phone=home_phone)
        cell_phone = normalize_phone(phone=cell_phone)
        work_phone = normalize_phone(phone=work_phone)
        phone_list = []

        if home_phone:
            home_phone = PhoneNumber(number=home_phone, type="H")
            if home_phone:
                phone_list.append(home_phone)

        if cell_phone:
            cell_phone = PhoneNumber(number=cell_phone, type="C")
            if cell_phone:
                phone_list.append(cell_phone)

        if work_phone:
            work_phone = PhoneNumber(number=work_phone, type="W")
            if work_phone:
                phone_list.append(work_phone)

        if phone_list:
            for number in phone_list:
                self.phone_numbers.append(number)

        if email:
            self.email_address = list(EmailAddress(email=email, active=True, primary=True))

        if addresses:
            address_list = []
            for address in addresses:
                if isinstance(address, dict):
                    address1 = address.get("address1", None)
                    address2 = address.get("address2", None)
                    city = address.get("city", None)
                    state = address.get("state", None)
                    zipcode = address.get("zipcode", None)
                    primary = address.get("primary", None)
                    if not isinstance(primary, bool):
                        primary = None
                    address_list.append(Address(address1=address1, address2=address2, city=city, state=state,
                                                zipcode=zipcode, primary=primary))
            self.set_addresses(addresses=address_list)

    @property
    def primary_address(self):
        if self._sa_instance_state.persistent or self._sa_instance_state.pending:
            current_primary = self.addresses.filter(Address._primary == True).first()
            if not current_primary:
                return None
            if current_primary:
                return current_primary
        else:
            return None

    def set_addresses(self, addresses=None):
        current_primary = self.primary_address
        if isinstance(addresses, list):
            primary_counter = 0
            for address in addresses:
                if isinstance(address, dict):
                    if address.get("primary", False):
                        primary_counter += 1
            if primary_counter > 0:
                if current_primary:
                    current_primary.primary = False
                    sa.session.add(current_primary)
                if primary_counter > 1:
                    for address in addresses:
                        address.primary = False
                    addresses[0].primary = True
            if not current_primary and primary_counter == 0:
                addresses[0].primary = True
            for address in addresses:
                self.addresses.append(address)

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, first_name):
        self._first_name = normalize_name(name=first_name)

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, last_name):
        self._last_name, self._suffix = normalize_lastname_suffix(last_name=last_name, suffix=self.suffix)

    @property
    def middle_name(self):
        return self._middle_name

    @middle_name.setter
    def middle_name(self, middle_name):
        self._middle_name = normalize_name(name=middle_name)

    @property
    def suffix(self):
        return self._suffix

    @suffix.setter
    def suffix(self, suffix):
        self._last_name, self._suffix = normalize_lastname_suffix(last_name=self.last_name, suffix=suffix)

    @property
    def sex(self):
        return self._sex

    @sex.setter
    def sex(self, sex):
        female_values = frozenset(["F", "FEMALE", "WOMAN", "GIRL"])
        male_values = frozenset(["M", "MALE", "MAN", "BOY"])
        unknown_values = frozenset(["U", "UNKNOWN"])
        other_values = frozenset(["O", "OTHER", "N/A"])
        if isinstance(sex, str):
            sex = str(sex).upper().strip()
            if sex in female_values:
                self._sex = 'F'
            if sex in male_values:
                self._sex = 'M'
            if sex in unknown_values:
                self._sex = 'U'
            if sex in other_values:
                self._sex = 'O'

    @property
    def dob(self):
        return self._dob

    @dob.setter
    def dob(self, dob):
        dob = normalize_dob(dob=dob)
        if dob:
            self._dob = dob.date()

    @property
    def home_phone(self):
        pass

    @property
    def cell_phone(self):
        pass

    @property
    def work_phone(self):
        pass

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        email = normalize_email(email=email)
        if email:
            self._email = email

    @property
    def ssn(self):
        return self._ssn

    @ssn.setter
    def ssn(self, ssn):
        n_ssn = normalize_ssn(ssn)
        if n_ssn:
            self._ssn = n_ssn

    @property
    def race(self):
        return self._race

    @race.setter
    def race(self, race):
        race = normalize_race(race=race)
        if race:
            self._race = race

    @property
    def ethnicity(self):
        return self._ethnicity

    @ethnicity.setter
    def ethnicity(self, ethnicity):
        ethnicity = normalize_ethnicity(ethnicity=ethnicity)
        if ethnicity:
            self._ethnicity = ethnicity

    @property
    def marital_status(self):
        return self._marital_status

    @marital_status.setter
    def marital_status(self, marital_status):
        marital_status = normalize_marital_status(status=marital_status)
        if marital_status:
            self._marital_status = marital_status

    @property
    def deceased(self):
        return self._deceased

    @deceased.setter
    def deceased(self, deceased):
        if self._deceased:
            pass
        else:
            status = normalize_deceased(value=deceased)
            if status:
                self._deceased = True
            else:
                self._deceased = False

    # TODO:  Group zip and address together, take city from zip lookup, fuzzy lookup for city state etc, lookup
    # By location and proximity to last zipcode, store addresses separately from patient? Zipcode type store?
    # make one utility address function that is called in the model unified
    # maybe one write property for patient address with address1, 2 and zip city etc as params and read only individ

    def check_hash(self):
        pass
        # included_hash_keys = (
        #     "first_name", "last_name", "middle_name", "sex", "dob", "ssn", "race", "ethnicity", "marital_status",
        #     "address1", "address2", "city", "state", "zip", "email", "home_phone", "cell_phone", "work_phone",
        #     "deceased")
        # hash_attributes = {}
        # for item in self.__dict__.keys():
        #     if item in included_hash_keys:
        #         hash_attributes[item] = str(self.__getattribute__(item))
        # json_hash_attributes = json.JSONEncoder().encode(hash_attributes)

    def before_insert(self):
        pass

    def before_update(self):
        pass


class PatientSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy Patient model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    #TODO: Review and finalize Marshmallow schema for Patient model
    id = fields.Int(dump_only=True)
    first_name = fields.String()
    last_name = fields.String()
    middle_name = fields.String()
    sex = fields.String()
    dob = fields.Date()
    ssn = fields.String()
    race = fields.String()
    ethnicity = fields.String()
    marital_status = fields.String()
    email = fields.Email()
    home_phone = fields.String()
    cell_phone = fields.String()
    work_phone = fields.String()
    deceased = fields.Boolean()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    row_hash = fields.String(dump_only=True)

    @post_load
    def make_patient(self, data):
        return Patient(**data)


patient_schema = PatientSchema()
