import os, hashlib, json
from random import randint
from app.security import *
from app.models.email_address import EmailAddress
from sqlalchemy.ext.hybrid import Comparator
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from marshmallow import fields, ValidationError, post_load, validates
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import sa, login_manager, ma
from app.models.role import Role
from app.models.address import Address
from app.models.phone_number import PhoneNumber
from app.models.extensions import BaseExtension
from app.utils.demographics import *


##################################################################################################
# SQL ALCHEMY USER MODEL DEFINITION
##################################################################################################

# UserMixin from flask_login
# is_authenticated() - Returns True if user has login credentials, else False
# is_active() - Returns True if useris allowed to login, else False.
# is_anonymous() - Returns False for logged in users
# get_id() - Returns unique identifier for user, as Unicode string
class User(UserMixin, sa.Model):
    ##################################
    # MODEL ATTRIBUTES AND PROPERTIES
    ##################################
    __tablename__ = 'user'
    __mapper_args__ = {'extension': BaseExtension()}

    id = sa.Column(sa.Integer, primary_key=True)
    _username = sa.Column("username", sa.Text, unique=True, index=True)
    email_addresses = sa.relationship("EmailAddress", back_populates="user", cascade="all, delete, delete-orphan")
    role_id = sa.Column(sa.Integer, sa.ForeignKey('role.id'), index=True)
    password_hash = sa.Column(sa.Text)
    last_password_hash = sa.Column(sa.Text)
    password_timestamp = sa.Column(sa.DateTime)
    _first_name = sa.Column("first_name", sa.Text, index=True)
    _last_name = sa.Column("last_name", sa.Text, index=True)
    _dob = sa.Column("dob", sa.Date, index=True)
    _sex = sa.Column("sex", sa.String(length=1))
    phone_numbers = sa.relationship("PhoneNumber", order_by=PhoneNumber.id.desc(), back_populates="user",
                                    lazy="dynamic",
                                    cascade="all, delete, delete-orphan")
    description = sa.Column(sa.Text)
    confirmed = sa.Column(sa.Boolean, default=False)
    active = sa.Column(sa.Boolean, default=True)
    addresses = sa.relationship("Address", order_by=Address.id.desc(), back_populates="user",
                                cascade="all, delete, delete-orphan")
    last_seen = sa.Column(sa.DateTime)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text)

    def __init__(self, username=None, first_name=None, last_name=None, dob=None, email=None, description=None,
                 phone_number=None, password=None, role_id=None, confirmed=False, active=True, **kwargs):
        self.username = username
        if email:
            email = EmailAddress(email=email, active=True, primary=True)
        if email:
            self.email_addresses.append(email)
            if str(email.email).lower() == current_app.config['UNKANI_ADMIN']:
                self.role = Role.query.filter_by(name='Super Admin').first()
        if password:
            self.password = password
        if isinstance(role_id, int):
            role = Role.query.get(role_id)
            if role:
                self.role = role
        if not self.role:
            self.role = Role.query.filter_by(default=True).first()

        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.description = description

        if phone_number:
            phone_number = PhoneNumber(number=phone_number, type="C", active=True)
            if phone_number:
                self.phone_numbers.append(phone_number)
        self.confirmed = confirmed
        self.active = active

    def __repr__(self):  # pragma: no cover
        __doc__ = """
        Represents user model instance as a username string"""
        return '<User %r>' % self.username

    #########################################
    # USER ATTRIBUTE NORMALIZATION PROPERTIES
    #########################################

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        if isinstance(username, str):
            username = username.upper().strip()
            self._username = username

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
        self._last_name = normalize_name(name=last_name)

    @property
    def sex(self):
        return self._sex

    @sex.setter
    def sex(self, sex):
        sex = normalize_sex(sex=sex)
        if sex:
            self._sex = sex

    @property
    def dob(self):
        return self._dob

    @property
    def dob_string(self):
        __doc__ = """
        Represent User's DOB as a string with format 'YYYY-MM-DD'
        """
        if self.dob:
            return self.dob.strftime('%Y-%m-%d')
        else:
            return None

    @dob.setter
    def dob(self, dob):
        dob = normalize_dob(dob=dob)
        if dob:
            self._dob = dob.date()

    @property
    def email(self):
        email_list = self.email_addresses
        primary_email = []
        if email_list:
            for email in email_list:
                if email.active and email.primary:
                    primary_email.append(email)
            if primary_email:
                return primary_email[0]

    @email.setter
    def email(self, email=None):
        if isinstance(email, str):
            email = EmailAddress(email=email, active=True, primary=True)
            if not email:
                raise ValueError("A valid email string is required to create a user.")
        elif isinstance(email, EmailAddress):
            email = email
        else:
            raise TypeError("A valid email string or Email object was not passed to the setter method for user.email")
        if email:
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
            raise ValueError("An email could not be created for the values provided to the setter method for email.")

    @property
    def phone(self):
        phone_list = self.phone_numbers
        if phone_list:
            for phone in phone_list:
                if phone.active:
                    return phone
        else:
            return None

    @phone.setter
    def phone(self, phone=None):
        if isinstance(phone, str):
            phone = PhoneNumber(number=phone, type='C', active=True)
            if not isinstance(phone, PhoneNumber):
                raise ValueError("A valid phone string is required to create a PhoneNumber object.")
        elif isinstance(phone, PhoneNumber):
            phone = phone
        else:
            raise TypeError(
                "A valid phone number string or PhoneNumber object was not passed to the setter method for user.phone")
        if phone:
            phone_list = self.phone_numbers
            phone_exists = False
            if phone_list:
                for item in phone_list:
                    if item.number == phone.number:
                        item.active = True
                        phone_exists = True
                    else:
                        if item.active:
                            item.active = False
            if not phone_exists:
                self.phone_numbers.append(phone)
        else:
            raise ValueError(
                "An phone number could not be created for the values provided to the setter method for phone.")

    ####################################
    # PASSWORD HASHING AND VERIFICATION
    ####################################
    @property
    def password(self):
        __doc__ = """
        Defines a property 'password'
        Raises an AttributeError if password property read is attempted"""
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        __doc__ = """
        Defines setter method for property 'password'.  The string passed as the password
        parameter is converted to salted hash and stored in database.  The former password hash
        is archived in the 'last_password_hash' attribute."""
        if self.password_hash:
            self.last_password_hash = self.password_hash
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha1', salt_length=8)
        self.password_timestamp = datetime.utcnow()

    def verify_password(self, password):
        __doc__ = """
        Compare inputted password hash with user's hashed password."""
        return check_password_hash(self.password_hash, password)

    def verify_last_password(self, password):
        __doc__ = """
        Compare inputted password hash with user's last hashed password."""
        return check_password_hash(self.last_password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        __doc__ = """
        Generates a Timed JSON Web Signature encoding the user's id using the application
        SECRET KEY.  Also encodes a key-value pair for account confirmation."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        __doc__ = """
        Loads Timed JSON web signature. Decodes using application Secret Key.  If user
        that is encrypted in the token is un-confirmed, sets user.confirmed boolean to True"""
        # TODO: Move confirmation boolean and process to email_address record instead of user
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        sa.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        __doc__ = """
        Generates a Timed JSON Web Signature encoding the user's id using the application
        SECRET KEY.  Also encodes a key-value pair for account password reset."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        __doc__ = """
        Decode and validate a Time JSON Web Signature supplied as the 'Token' variable. Ensure
        that the id encoded in the token matches the expected user.  Update the user password attribute
        with the password supplied in the parameter 'new_password'."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        sa.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        __doc__ = """
        Generates a Timed JSON Web Signature encoding the user's id using the application
        SECRET KEY.  Also encodes a key-value pair for email change and validation."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def process_change_email_token(self, token):
        __doc__ = """
        Decode and validate a Time JSON Web Signature supplied as the 'Token' variable. Ensure
        that the id encoded in the token matches the expected user.  Check for a 'change_password'
        key in the token with a value matching the current user id.  If match exists for specified
        user, update the user email with the email supplied in the token as 'new_email'."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            raise ValueError("Invalid token provided.")
        if data.get('change_email') != self.id:
            raise ValueError("Token provided did not match the logged in user's identity.")
        new_email = data.get('new_email', None)
        if not new_email:
            raise ValueError("An email address was not included in the change email request token.")
        matching_email = sa.session.query(EmailAddress).filter(EmailAddress.user_id == self.id).filter(
            EmailAddress._email == new_email).first()
        if matching_email:
            self.email = matching_email
            sa.session.add(self)
        else:
            raise ValueError("A matching email for the logged-in user could not be found.")

    def verify_email(self, email):
        __doc__ = """
        Helper method to compare a supplied email with the user's email.  Returns True
        if email matches, False if not."""
        if isinstance(email, str):
            email = str(email).upper().strip()
            if self.email.email == email:
                return True
            else:
                return False
        if isinstance(email, EmailAddress):
            if self.email.email == email.email:
                return True
            else:
                return False

    def verify_previous_email(self, email):
        __doc__ = """
        Helper method to compare a supplied email with the user's previous email.  Returns True
        if email matches, False if not."""
        email = str(email).strip().upper()
        previous_email = sa.session.query(EmailAddress).join(User).filter(EmailAddress.user == self).filter(
            EmailAddress._primary == False).order_by(EmailAddress.updated_at.desc()).first()
        if previous_email and previous_email.email == email:
            return True
        else:
            return False

    #####################################
    # USER PERMISSION LEVEL COMPARISON
    #####################################
    def has_higher_permission(self, user):
        __doc__ = """
        User Method:  Helper method that accepts either the userid integer
        of another user, or the user object of another user.
        The method looks up compares the permission level of the other user's role with
        the permission level of the base user object's role.  Returns True of the
        base user object's permission level is higher than the other user's
        permission level.  Else, the method returns False.

        Used to protect access to actions performed on other users.


        param <user>:
            If an integer is pased, the function expects an integer userid to be
            supplied as the 'user' parameter.  The method then looks up
            the corresponding user record to perform the comparison.

            Non integer value passed, the function expects a complete user object
            to be supplied.  The method then compares the base user object to the
            user object supplied as a parameter.
            This configuration helps to avoid un-necessary object lookup.

        """
        other_user = user
        if isinstance(other_user, int):
            other_user = User.query.get(user)
        if not other_user:
            return True
        if self.role.level > other_user.role.level:
            return True
        else:
            return False

    @staticmethod
    def compare_permission_level(user1, user2):
        __doc__ = """
        User Method:  Helper method that accepts either the userid integers
        of two users to be compared, or the user objects of the two users.
        The method looks up compares the permission level of first users role with
        the permission level of the second users role.  Returns True if the user
        specified with the parameter user2. has a higher permission level than the
        user specified with parameter user2.  Else, the method returns False.

        Used to protect access to actions performed on other users by permission
        level as appropriate.

        If an integer value is passed as either <user1> or <user2>, the corresponding
        user with that id looked up in the database.  If the user does not exist, a validation
        error is raised.  If <user1> or <user2> are not integers, a user object is assumed
        to be passed to the function.

        """
        if isinstance(user1, int):
            user1 = User.query.get(user1)
        if isinstance(user2, int):
            user2 = User.query.get(user2)
        if not user1:
            raise ValidationError('User1 does not exist.')
        if not user2:
            raise ValidationError('User2 does not exist.')
        if user1.role.level > user2.role.level:
            return True
        else:
            return False

    def has_access_to_user_operation(self, user, other_permissions=[None], self_permissions=[None]):
        __doc__ = """
        User Method:
        Helper function that checks whether the base user object should have
        access to perform operations on their own user record, or another user record.

        The method first checks whether the identity of the user passed in the 'user' parameter matches the current
        supplied identity in the session and request via Flask-Principal's Permission object.  If the identities match,
        the method then checks the param <self_permissions> for a list of Flask-Principal permission objects that are
        required to be supplied by the base user to perform operations on their own user record. If
        the base user object has all of the permissions listed in the param <self_permissions>, as tested by
        performing <self_permission>.can(), the base user is determined to have access to perform the given operation
        on their own user object and the method returns True.  If the param <self_permissions> is None, the method
        will also return True.

        If the base user object does not match the current identity, the list of permissions supplied in the param
        <other_permissions> is checked against the current user identity.  If the base user object has all of the
        permissions listed in the param <other_permissions>, as tested by performing <other_permission>.can(),
        the base user is determined to have access to perform the given operation on the user object specified in the
        param <user> and the method returns True.  If the param <other_permissions> is None, the method
        will also return True.

        param <user>:
            Either the integer user id of the user to be compared to the base user object, or the fully
            qualified user object to be compared with the base user.  If an integer input is detected, the
            user with that corresponding id is looked up in the database.  Otherwise, a fully qualified user
            object is assumed.


        param <self_permissions>:
            A list of Flask-Principal permission objects that must be provided by the current identity in order
            to perform the protected user operation on the self-same user object.  If the list is set to None, no
            additional permissions are required.

            Default is: None

        param <other_permissions>:
            A list of Flask-Principal permission objects that must be provided by the current identity in order
            to perform the protected user operation on the user specified in the param <user>.
            If the list is set to None, no additional permissions are required.

            Default is: None

        """
        if isinstance(user, int):
            user = User.query.get(user)
        if not user:
            raise ValidationError("User could not be found.")
        has_access = False
        if test_user_permission(user.id):
            has_access = True
            if self_permissions[0] is not None:
                for permission in self_permissions:
                    if not permission.can():
                        has_access = False
                        break
        elif self.has_higher_permission(user=user):
            has_access = True
            if other_permissions[0] is not None:
                for permission in other_permissions:
                    if not permission.can():
                        has_access = False
                        break
        if has_access:
            return True
        return False

    #####################################
    # AVATAR HASHING AND GRAVATAR SUPPORT
    #####################################
    @property
    def gravatar(self):
        primary_email = self.email
        if not primary_email:
            return None
        elif isinstance(primary_email, EmailAddress):
            return primary_email.gravatar()

    #####################################
    # MISC UTILITY PROPERTIES AND METHODS
    #####################################

    @property
    def joined_year(self):
        __doc__ = """
        Represents the year the user record was created with format 'YYYY'"""
        if self.created_at:
            return self.created_at.strftime('%Y')
        else:
            return None

    def ping(self):
        __doc__ = """
        Ping function called before each request initiated by authenticated user.
        Stores timestamp of last request for the user in the 'last_seen' attribute."""
        self.last_seen = datetime.utcnow()
        sa.session.add(self)

    ##############################################################################################
    # USER API SUPPORT
    ##############################################################################################

    def generate_api_auth_token(self, expiration=600):
        __doc__ = """
        Generates a Time JSON Web Signature token, with an expiration of 600 seconds
        by default.  Uses the application SECRET KEY to encrypt the token.  Token encrypts the
        user.id attribute with a key of 'id' for future identification use.  The token is supplied
        in an ascii format, for use with API requests."""
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({'id': self.id}).decode('ascii')
        return token

    @staticmethod
    def verify_api_auth_token(token):
        __doc__ = """
        User Method:  verify_api_auth_token takes a token and,
        if found valid, returns the user object stored in it.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(int(data['id']))

    ##############################################################################################
    # USER RANDOMIZATION UTILITIES
    ##############################################################################################
    def randomize_user(self, demo_dict=None):
        __doc__ = """
        User Method: acts upon an initialized user object and randomizes key attributes
        of the user.
        
        Demo Dict:  Dictionary of demographic data supplied if needed.  Else, randomly created
        
        Password:  If a password is supplied in the environment variable 'TEST_USER_PASSWORD'
        that password is assigned to the user.  If not present, the password is randomized.
        """
        if not isinstance(demo_dict, dict):
            demo_dict = list(random_demographics(number=1))[0]
            demo_dict = dict(demo_dict)
        self._first_name = demo_dict.get("first_name", None)
        self._last_name = demo_dict.get("last_name", None)
        self._dob = demo_dict.get("dob", None)
        self.email = demo_dict.get("email", None)
        self.username = (self.first_name + "." + self.last_name + str(randint(0, 1000)))
        self.sex = demo_dict.get("sex", None)
        addr = Address()
        addr._address1 = demo_dict.get("address1", None)
        addr._address2 = demo_dict.get("address2", None)
        addr._city = demo_dict.get("city", None)
        addr._state = demo_dict.get("state", None)
        addr._zipcode = demo_dict.get("zipcode", None)
        addr.active = True
        addr.primary = True
        self.addresses.append(addr)
        self.phone = demo_dict.get("cell_phone", None)
        self.description = random_description(max_chars=200)

    @staticmethod
    def initialize_admin_user():
        __doc__ = """
        User staticmethod: Generates and commits a super_admin user.  Loads user
        attributes stored as environment variables specified as 'UNKANI_ADMIN_*.
        Executed on deployment and db creation.  Checks for existing user with admin's
        email before attempting to create a new one."""
        admin_user_username = os.environ.get('UNKANI_ADMIN_USERNAME')
        user = User.query.filter(User._username == str(admin_user_username).upper()).first()
        if user is None:
            user = User(email=os.environ.get('UNKANI_ADMIN_EMAIL'))
            user.username = os.environ.get('UNKANI_ADMIN_USERNAME')
            user.password = os.environ.get('UNKANI_ADMIN_PASSWORD')
            user.first_name = os.environ.get('UNKANI_ADMIN_FIRST_NAME')
            user.last_name = os.environ.get('UNKANI_ADMIN_LAST_NAME')
            user.phone = os.environ.get('UNKANI_ADMIN_PHONE')
            user.confirmed = True
            sa.session.add(user)
            sa.session.commit()

    def generate_row_hash(self):
        data = {"username": self.username, "first_name": self.first_name, "last_name": self.last_name,
                "dob": self.dob_string, "sex": self.sex}
        for key in data:
            data[key] = str(data[key])
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        pass
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        pass
        self.row_hash = self.generate_row_hash()


###################################################
# AnonymousUser custom class definition
###################################################
# Created for future use.  May need to be augmented from Flask-Login standard
# to accommodate custom attributes in the user model, not handled by default
# anonymous user object.
class AnonymousUser(AnonymousUserMixin):
    pass


login_manager.anonymous_user = AnonymousUser


###################################################
# Flask Login - User Loader Function
###################################################
# Callback function, receives a user identifier and
# returns either user object or None
# Used by Flask-Login to set current_user()
@login_manager.user_loader
def load_user(user_id):
    __doc__ = """
    Callback function for User model.  Receives a user id and
    returns either an associated userid for a valid user record, or
    None if no record exists.  Used by Flask-Login to set the
    current_user attribute."""
    return User.query.get(int(user_id))


##################################################################################################
# MARSHMALLOW USER SCHEMA DEFINITION FOR OBJECT SERIALIZATION AND INPUT VALIDATION
##################################################################################################

class UserSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy User model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    id = fields.Int(dump_only=True)
    # email_prop = User.__mapper__.get_property('email')
    # email = property2field(email_prop)
    # email = fields.Email(attribute='email', dump_only=True)
    # username = fields.String(dump_only=True)
    # password = fields.String(load_only=True)
    first_name = fields.String()
    last_name = fields.String()
    # dob = fields.Date()
    # phone = fields.String()
    # description = fields.String()
    confirmed = fields.Boolean(dump_only=True)
    active = fields.Boolean(dump_only=True)
    # gravatar_url = fields.Method("gravatar", dump_only=True)
    role_id = fields.Int(dump_only=True)
    role_name = fields.Method("get_role_name", dump_only=True)
    create_timestamp = fields.DateTime(dump_only=True)
    last_seen = fields.DateTime(dump_only=True)

    def get_role_name(self, user):
        __doc__ = """
        Returns the name of the user's role as a string."""
        return user.role.name


class UserSchemaCreate(UserSchema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy User model.  Extends base User model schema.
    Defines updated read-only and write only attributes for User object creation (POST)."""
    email = fields.Email(required=True)
    username = fields.String(required=True)
    password = fields.String(required=True, load_only=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)

    @post_load
    def make_user(self, data):
        return User(**data)

    @validates('email')
    def validate_email(self, value):
        if User.query.filter_by(email=value).first():
            raise ValidationError('An account with the email {} already exists.'.format(value))

    @validates('username')
    def validate_username(self, value):
        if User.query.filter_by(username=value).first():
            raise ValidationError('An account with the username {} already exists.'.format(value))


class UserSchemaUpdate(UserSchema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy User model.  Extends base User model schema.
    Defines updated read-only and write only attributes for User object updates (PATCH and PUT)."""
    id = fields.Int(required=True)
    email = fields.Email(dump_only=False)
    username = fields.String(dump_only=False)

    @post_load
    def update_user(self, data):
        return User(**data)


# Assign Schema functions to variables, with handling of multiple instances pre-configured
# Schema variables are imported into API module for use with serializing / de-serializing
user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_schema_create = UserSchemaCreate()
users_schema_create = UserSchemaCreate(many=True)
user_schema_update = UserSchemaUpdate()
users_schema_update = UserSchemaUpdate(many=True)
