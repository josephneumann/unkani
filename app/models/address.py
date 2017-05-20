from app import sa, ma
from marshmallow import fields, ValidationError, post_load, validates
from app.utils.demographics import *
from app.models.extensions import BaseExtension


class Address(sa.Model):
    _tablename__ = 'address'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True)
    _address1 = sa.Column(sa.Text)
    _address2 = sa.Column(sa.Text)
    _city = sa.Column("city", sa.Text)
    _state = sa.Column("state", sa.String(2))
    _zipcode = sa.Column("zipcode", sa.Text)
    _primary = sa.Column("primary", sa.Boolean)
    _active = sa.Column("active", sa.Boolean, default=True)
    patient_id = sa.Column(sa.Integer, sa.ForeignKey('patient.id'))
    patient = sa.relationship("Patient", back_populates="addresses")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    user = sa.relationship("User", back_populates="addresses")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text)

    def __init__(self, address1=None, address2=None, city=None, state=None, zipcode=None, active=True, primary=False,
                 **kwargs):
        address1 = address1
        address2 = address2
        city = city
        state = state
        zipcode = zipcode
        self.set_address(address1=address1, address2=address2, city=city, state=state, zipcode=zipcode)
        self._active = active
        primary = primary
        self._primary = primary

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        n_city, n_state, n_zip = normalize_city_state(state=state)
        if n_state:
            if self.zipcode:
                current_zip_object = lookup_zipcode(self.zipcode)
                if n_state != current_zip_object.State:
                    self._zipcode = None
            if self.city:
                zip_list = normalize_city_state(city=self.city, state=n_state)
                current_city_state_object = zip_list[0]
                if not current_city_state_object:
                    self._city = None
            self._state = n_state

    @property
    def zipcode(self):
        return self._zipcode

    @zipcode.setter
    def zipcode(self, zipcode):
        zipcode = lookup_zipcode(zipcode=zipcode)
        if zipcode:
            self._zipcode = zipcode.Zipcode
            self._city = str(zipcode.City).upper()
            self._state = zipcode.State

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, city):
        if city:
            self._city = str(city).upper().strip()

    @property
    def address1(self):
        return self._address1

    @address1.setter
    def address1(self, address1):
        n_address1 = None
        if address1:
            n_address1 = str(address1).strip().upper()
        if n_address1:
            self._address1 = n_address1

    @property
    def address2(self):
        return self._address2

    @address2.setter
    def address2(self, address2):
        n_address2 = None
        if address2:
            n_address2 = str(address2).strip().upper()
        if n_address2:
            self._address2 = n_address2

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
    def active(self, active=True):
        if isinstance(active, bool):
            self._active = active

    def set_address(self, address1=None, address2=None, city=None, state=None, zipcode=None):
        address_dict = normalize_address(address1=address1, address2=address2, city=city, state=state, zipcode=zipcode)
        self._address1 = address_dict.get("address1", None)
        self._address2 = address_dict.get("address2", None)
        self._city = address_dict.get("city", None)
        self._state = address_dict.get("state", None)
        self._zipcode = address_dict.get("zipcode", None)
        # element_hierarchy = {"state":1, "city":2, "zipcode":3, "address1":4, "address2":4}

    def before_insert(self):
        pass

    def before_update(self):
        pass


class AddressSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy Address model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    address1 = fields.String()
    address2 = fields.String()
    city = fields.String()
    zip = fields.String()
    state = fields.String()
