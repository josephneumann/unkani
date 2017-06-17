from app import sa, ma
from marshmallow import fields, post_load
from app.utils.demographics import *
from app.models import Address, EmailAddress, PhoneNumber
from app.models.extensions import BaseExtension
import hashlib, json


class Patient(sa.Model):
    __tablename__ = 'patient'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True)
    _first_name = sa.Column("first_name", sa.Text, index=True)
    _last_name = sa.Column("last_name", sa.Text, index=True)
    _middle_name = sa.Column("middle_name", sa.Text)
    _suffix = sa.Column("suffix", sa.Text)
    _sex = sa.Column("sex", sa.String(1))
    _dob = sa.Column("dob", sa.Date, index=True)
    _ssn = sa.Column("ssn", sa.Text)
    _race = sa.Column("race", sa.Text)
    _ethnicity = sa.Column("ethnicity", sa.Text)
    _marital_status = sa.Column("marital_status", sa.String(1))
    _deceased = sa.Column("deceased", sa.Boolean)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text)
    email_addresses = sa.relationship("EmailAddress", back_populates="patient", cascade="all, delete, delete-orphan")
    addresses = sa.relationship("Address", order_by=Address.id.desc(), back_populates="patient", lazy="dynamic",
                                cascade="all, delete, delete-orphan")
    phone_numbers = sa.relationship("PhoneNumber", order_by=PhoneNumber.id.desc(), back_populates="patient",
                                    lazy="dynamic",
                                    cascade="all, delete, delete-orphan")

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
        phone_list = self.phone_numbers
        if phone_list:
            home_phone = None
            for phone in phone_list:
                if phone.type == "H":
                    home_phone = phone
            if home_phone:
                return home_phone.number
            else:
                return None
        else:
            return None

    @property
    def cell_phone(self):
        phone_list = self.phone_numbers
        if phone_list:
            cell_phone = None
            for phone in phone_list:
                if phone.type == "C":
                    cell_phone = phone
            if cell_phone:
                return cell_phone.number
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
                if phone.type == "W":
                    work_phone = phone
            if work_phone:
                return work_phone.number
            else:
                return None
        else:
            return None

    @property
    def email(self):
        email_list = self.email_addresses
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
            email_list = self.email_addresses
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
    def ssn(self):
        return format_ssn(ssn=self._ssn)

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
        self._first_name = demo_dict.get("first_name", None)
        self._last_name = demo_dict.get("last_name", None)
        self._middle_name = demo_dict.get("middle_name", None)
        self._suffix = demo_dict.get("suffix", None)
        self._dob = demo_dict.get("dob", None)
        self.email = demo_dict.get("email", None)
        self._sex = demo_dict.get("sex", None)
        self.ssn = demo_dict.get("ssn", None)
        self._race = demo_dict.get("race", None)
        self._ethnicity = demo_dict.get("ethnicity", None)
        self._marital_status = demo_dict.get("marital_status", None)
        self._deceased = demo_dict.get("deceased", False)

        addr = Address()
        addr._address1 = demo_dict.get("address1", None)
        addr._address2 = demo_dict.get("address2", None)
        addr._city = demo_dict.get("city", None)
        addr._state = demo_dict.get("state", None)
        addr._zipcode = demo_dict.get("zipcode", None)
        addr.active = True
        addr.primary = True
        self.addresses.append(addr)

        phone_list = []
        home_phone = demo_dict.get("home_phone", None)
        cell_phone = demo_dict.get("cell_phone", None)
        work_phone = demo_dict.get("work_phone", None)

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

    def generate_row_hash(self):
        if self.dob:
            dob_str = self.dob.strftime("YYYYMMDD")
        else:
            dob_str = None
        data = {"first_name": self.first_name, "last_name": self.last_name,
                "middle_name": self.middle_name, "sex": self.sex, "dob": dob_str,
                "ssn": self.ssn, "race": self.race, "ethnicity": self.ethnicity,
                "marital_status": self.marital_status, "deceased": self.deceased, "suffix": self.suffix}
        for key in data:
            data[key] = str(data[key])
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()


class PatientSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy Patient model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    # TODO: Review and finalize Marshmallow schema for Patient model
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
