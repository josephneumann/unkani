import os, hashlib, json
from flask import current_app, g
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from flask_login import UserMixin, AnonymousUserMixin, current_user
from marshmallow import fields, ValidationError
from itsdangerous import TimedJSONWebSignatureSerializer as TimedSerializer, JSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import sa, login_manager, ma
from app.models.email_address import EmailAddress
from app.models.role import Role
from app.models.address import Address, AddressSchema
from app.models.phone_number import PhoneNumber
from app.models.extensions import BaseExtension
from app.models.app_group import user_app_group, AppGroup, AppGroupSchema
from app.utils.demographics import *
from app.utils.general import json_serial, url_for


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
    username = sa.Column("username", sa.Text, unique=True, index=True)
    role_id = sa.Column(sa.Integer, sa.ForeignKey('role.id'), index=True)
    first_name = sa.Column("first_name", sa.Text, index=True)
    last_name = sa.Column("last_name", sa.Text, index=True)
    dob = sa.Column("dob", sa.Date, index=True)
    sex = sa.Column("sex", sa.Text())
    description = sa.Column(sa.Text)
    confirmed = sa.Column(sa.Boolean, default=False)
    active = sa.Column(sa.Boolean, default=True)
    password_hash = sa.Column(sa.Text)
    last_password_hash = sa.Column(sa.Text)
    password_timestamp = sa.Column(sa.DateTime)
    email_addresses = sa.relationship("EmailAddress", back_populates="user", lazy="dynamic",
                                      cascade="all, delete, delete-orphan")
    phone_numbers = sa.relationship("PhoneNumber", order_by=PhoneNumber.id.desc(), back_populates="user",
                                    lazy="dynamic",
                                    cascade="all, delete, delete-orphan")
    addresses = sa.relationship("Address", order_by=Address.id.desc(), back_populates="user",
                                lazy="dynamic", cascade="all, delete, delete-orphan")
    app_groups = sa.relationship('AppGroup',
                                 secondary=user_app_group,
                                 back_populates='users')
    last_seen = sa.Column(sa.DateTime)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    updated_at = sa.Column(sa.DateTime)
    row_hash = sa.Column(sa.Text, index=True)

    def __init__(self, username=None, first_name=None, last_name=None, dob=None, description=None,
                 password=None, sex=None, role_id=None, confirmed=False, active=True, **kwargs):
        self.username = username
        self.password = password
        self.dob = dob
        self.first_name = first_name
        self.last_name = last_name
        self.sex = sex
        self.description = description
        self.confirmed = confirmed
        self.active = active

        if isinstance(role_id, int):
            role = Role.query.get(role_id)
            if role:
                self.role = role

        if not self.role:
            role = Role.query.filter_by(default=True).first()
            self.role = role

    def __repr__(self):  # pragma: no cover
        __doc__ = """
        Represents user model instance as a username string"""
        return '<User {}:{}>'.format(self.id, self.username)

    ############################################
    # USER PROPERTY HANDLERS FOR RELATED MODELS
    ############################################

    @hybrid_property
    def email(self):
        """Returns the primary email for the account.
        Users may only have one Active and Primary email per account
        All other emails (old emails) must be inactive and non primary
        """
        return self.email_addresses.filter(EmailAddress.primary == True).filter(EmailAddress.active == True).first()

    @email.setter
    def email(self, email=None):
        raise AttributeError('This property is read-only.')

    @property
    def phone_number(self):
        """Returns the primary phone number for the account.
        Users may only have one Active and Primary phone number per account
        All other phone numbers (old) must be inactive and non primary
        """
        return self.phone_numbers.filter(PhoneNumber.primary == True).filter(PhoneNumber.active == True).first()

    @phone_number.setter
    def phone_number(self, phone=None):
        raise AttributeError('This property is read-only.')

    @property
    def address(self):
        """Returns the primary address for the account.
        Users may only have one Active and Primary address per account
        All other addresses (old) must be inactive and non primary
        """
        return self.addresses.filter(Address.primary == True).filter(Address.active == True).first()

    @address.setter
    def address(self, address=None):
        raise AttributeError('This property is read-only.')

    ####################################
    # RESOURCE URL BUILDER
    ####################################
    def get_url(self):
        return url_for('api_v1.get_user', userid=self.id, _external=True)

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
        if password:
            pw_hash = unkani_password_hasher(password=password)
            if self.password_hash:
                if pw_hash != self.password_hash:
                    self.last_password_hash = self.password_hash
                    self.password_hash = pw_hash
                    self.password_timestamp = datetime.utcnow()
            else:
                self.password_hash = pw_hash
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
        s = TimedSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        __doc__ = """
        Loads Timed JSON web signature. Decodes using application Secret Key.  If user
        that is encrypted in the token is un-confirmed, sets user.confirmed boolean to True"""
        # TODO: Move confirmation boolean and process to email_address record instead of user
        s = TimedSerializer(current_app.config['SECRET_KEY'])
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
        s = TimedSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        __doc__ = """
        Decode and validate a Time JSON Web Signature supplied as the 'Token' variable. Ensure
        that the id encoded in the token matches the expected user.  Update the user password attribute
        with the password supplied in the parameter 'new_password'."""
        s = TimedSerializer(current_app.config['SECRET_KEY'])
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
        s = TimedSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def process_change_email_token(self, token):
        __doc__ = """
        Decode and validate a Time JSON Web Signature supplied as the 'Token' variable. Ensure
        that the id encoded in the token matches the expected user.  Check for a 'change_password'
        key in the token with a value matching the current user id.  If match exists for specified
        user, update the user email with the email supplied in the token as 'new_email'."""
        s = TimedSerializer(current_app.config['SECRET_KEY'])
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
            EmailAddress.email == new_email).first()
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
            EmailAddress.primary == False).order_by(EmailAddress.updated_at.desc()).first()
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

    def is_accessible(self, requesting_user, other_permissions=[], self_permissions=[]):
        __doc__ = """
        User Method:
        Helper function that checks whether the base user object should be
        accessible to perform operations on their own user record, or another user record.

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
        if requesting_user:
            if isinstance(requesting_user, int):
                requesting_user = User.query.get(requesting_user)
                print('detected userid input')
                if not requesting_user:
                    raise ValueError("User could not be found.")
        else:
            if current_user and not current_user.is_anonymous():
                requesting_user = current_user
            else:
                raise ValueError("No user was supplied and no logged in user was detected.")

        # Stuff to check is user is accessing their own record
        if self.id == requesting_user.id:
            print('user is themself!')
            # If self_permissions param is set, make sure all of those permissions are allowed
            if self_permissions:
                print('checking self permissions')
                for perm in self_permissions:
                    if not perm.can():
                        print('self permission failure')
                        return False
        # Stuff to check is user is accessing another user
        else:
            print('checking other user permissions')
            # Check for overlap between app groups.  If no shared group, deny access
            if not (set(self.app_groups) & set(requesting_user.app_groups)):
                print('app group overlap not detected')
                return False
            if not requesting_user.has_higher_permission(user=self):
                print('role permission level check failure')
                return False
            if other_permissions:
                print('checking other permissions')
                for perm in other_permissions:
                    if not perm.can():
                        print('permission failure: {}'.format(perm))
                        return False
        print('Everything passes!')
        return True

    #####################################
    # AVATAR HASHING AND GRAVATAR SUPPORT
    #####################################
    def gravatar_url(self, size=100):
        """Returns Gravatar URL from primary user EmailAddress"""
        primary_email = self.email
        if primary_email:
            return primary_email.gravatar_url(size=size)

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

    @property
    def dob_string(self):
        __doc__ = """
        Represent User's DOB as a string with format 'YYYY-MM-DD'
        """
        if self.dob:
            return self.dob.strftime('%Y-%m-%d')
        else:
            return None

    ##############################################################################################
    # USER API SUPPORT
    ##############################################################################################

    def generate_api_auth_token(self, expiration=600):
        __doc__ = """
        Generates a Time JSON Web Signature token, with an expiration of 600 seconds
        by default.  Uses the application SECRET KEY to encrypt the token.  Token encrypts the
        user.id attribute with a key of 'id' for future identification use.  The token is supplied
        in an ascii format, for use with API client.py."""
        s = TimedSerializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({'id': self.id}).decode('ascii')
        return token

    @staticmethod
    def verify_api_auth_token(token):
        __doc__ = """
        User Method:  verify_api_auth_token takes a token and,
        if found valid, returns the user object stored in it.
        """
        s = TimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(int(data['id']))

    ##############################################################################################
    # USER RANDOMIZATION METHODS
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
        self.first_name = demo_dict.get("first_name", None)
        self.last_name = demo_dict.get("last_name", None)
        self.dob = demo_dict.get("dob", None)
        self.email_addresses.append(EmailAddress(email=demo_dict.get("email", None), primary=True, active=True))
        self.username = demo_dict.get("username", None)
        self.sex = demo_dict.get("sex", None)
        addr = Address()
        addr.address1 = demo_dict.get("address1", None)
        addr.address2 = demo_dict.get("address2", None)
        addr.city = demo_dict.get("city", None)
        addr.state = demo_dict.get("state", None)
        addr.zipcode = demo_dict.get("zipcode", None)
        addr.active = True
        addr.primary = True
        self.addresses.append(addr)
        self.phone_numbers.append(PhoneNumber(number=demo_dict.get("mobile_phone", None), type='MOBILE', primary=True))
        self.description = random_description(max_chars=200)
        self.app_groups.append(AppGroup.query.filter(AppGroup.name == 'DEMO GROUP').first())

    ##############################################################################################
    # ADMIN USER CREATION METHOD
    ##############################################################################################
    @staticmethod
    def initialize_admin_user():
        __doc__ = """
        User staticmethod: Generates and commits a super_admin user.  Loads user
        attributes stored as environment variables specified as 'UNKANI_ADMIN_*.
        Executed on deployment and db creation.  Checks for existing user with admin's
        email before attempting to create a new one."""
        admin_user_username = os.environ.get('UNKANI_ADMIN_USERNAME')
        user = User.query.filter(User.username == str(admin_user_username).upper()).first()
        if user is None:
            user = User()
            email = validate_email(os.environ.get('UNKANI_ADMIN_EMAIL'))
            email_obj = EmailAddress(email=email, primary=True, active=True)
            user.email_addresses.append(email_obj)
            user.username = normalize_name(os.environ.get('UNKANI_ADMIN_USERNAME'))
            user.password = os.environ.get('UNKANI_ADMIN_PASSWORD')
            user.first_name = normalize_name(os.environ.get('UNKANI_ADMIN_FIRST_NAME'))
            user.last_name = normalize_name(os.environ.get('UNKANI_ADMIN_LAST_NAME'))
            user.role = Role.query.filter_by(name='Super Admin').first()
            for ag in AppGroup.query.all():
                if ag not in user.app_groups:
                    user.app_groups.append(ag)
            user.description = 'Unkani creator and lead developer'
            user.sex = 'MALE'
            user.dob = validate_dob(dob='19900211')

            admin_phone = os.environ.get('UNKANI_ADMIN_PHONE')
            if admin_phone:
                try:
                    user.phone_number = validate_phone(phone=admin_phone)
                except:
                    pass
            user.confirmed = True
            sa.session.add(user)
            sa.session.commit()

    ##############################################################################################
    # OBJECT HASHING METHODS
    ##############################################################################################

    def generate_row_hash(self):
        data = {"username": self.username, "first_name": self.first_name, "last_name": self.last_name,
                "dob": self.dob_string, "sex": self.sex, "role_id": self.role_id, "password_hash": self.password_hash,
                "last_password_hash": self.last_password_hash, "password_timestamp": self.password_timestamp,
                "description": self.description, "confirmed": self.confirmed, "active": self.active,
                "last_seen": self.last_seen, "created_at": self.created_at, "updated_at": self.updated_at}
        data_str = json.dumps(data, sort_keys=True, default=json_serial)
        data_hash = hashlib.sha1(data_str.encode('utf-8')).hexdigest()
        return data_hash

    def before_insert(self):
        self.row_hash = self.generate_row_hash()

    def before_update(self):
        self.row_hash = self.generate_row_hash()

    ##############################################################################################
    # USER SERIALIZATION METHOD
    ##############################################################################################

    def dump(self):
        schema = UserSchema()
        user = schema.dump(self).data
        return user


##################################################################################################
# MARSHMALLOW USER SCHEMA DEFINITION FOR OBJECT SERIALIZATION
##################################################################################################

class UserSchema(ma.Schema):
    """Marshmallow schema, associated with SQLAlchemy User model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""

    class Meta:
        # exclude = ()
        ordered = False

    id = fields.Int(dump_only=True)
    first_name = fields.String(attribute='first_name', dump_only=True)
    last_name = fields.String(attribute='last_name', dump_only=True)
    username = fields.String(attribute='username', dump_only=True)
    dob = fields.Date(attribute='dob', dump_only=True)
    sex = fields.String(attribute='sex', dump_only=True)
    description = fields.String(attribute='description', dump_only=True)
    confirmed = fields.Boolean(attribute='confirmed', dump_only=True)
    active = fields.Boolean(attribute='active', dump_only=True)
    role = fields.Method('get_role', dump_only=True)
    email_address = fields.Method('get_email', dump_only=True)
    phone_number = fields.Method('get_phone', dump_only=True)
    address = fields.Method('get_address', dump_only=True)
    gravatar_url = fields.Url(attribute='gravatar', dump_only=True)
    created_at = fields.DateTime(attribute='created_at', dump_only=True)
    updated_at = fields.DateTime(attribute='updated_at', dump_only=True)
    last_seen = fields.DateTime(attribute='last_seen', dump_only=True)
    row_hash = fields.String(attribute='row_hash', dump_only=True)
    app_groups = fields.Method('get_app_groups', dump_only=True)
    self_url = fields.Method('get_self_url', dump_only=True)

    def get_role(self, user):
        """Returns a dict representing the user's role"""
        return user.role.dump()

    def get_email(self, user):
        return user.email.email

    def get_phone(self, user):
        if user.phone_number:
            return user.phone_number.formatted_phone

    def get_address(self, user):
        if user.address:
            schema = AddressSchema(only=('address1', 'address2', 'city', 'state', 'zipcode'))
            address_data, x = schema.dump(user.address)
            return address_data
        else:
            return None

    def get_app_groups(self, user):
        schema = AppGroupSchema(only=('id', 'name'))
        app_groups = []
        for x in user.app_groups:
            data, _ = schema.dump(x)
            app_groups.append(data)
        return app_groups

    def get_self_url(self, user):
        return user.get_url()


##################################################################################################
# USER-RELATED UTILITY FUNCTIONS
##################################################################################################

def unkani_password_hasher(password):
    return generate_password_hash(password, method='pbkdf2:sha1', salt_length=8)


def lookup_user_by_email(email):
    if isinstance(email, EmailAddress):
        email = email.email
    try:
        n_email = validate_email(email=email)
        return sa.session.query(User).join(EmailAddress).filter(EmailAddress.email == n_email).first()
    except ValueError:
        return None


def lookup_user_by_username(username):
    try:
        n_username = normalize_name(name=username)
        return sa.session.query(User).filter(User.username == n_username).first()
    except ValueError:
        return None


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
