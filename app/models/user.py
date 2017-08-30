import os, hashlib, json
from flask import current_app, g
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin, AnonymousUserMixin, current_user
from marshmallow import fields, ValidationError
from itsdangerous import TimedJSONWebSignatureSerializer as TimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import sa, login_manager, ma
from app.flask_sendgrid import send_email
from app.models.phone_number import PhoneNumberAPI
from app.models.email_address import EmailAddress, EmailAddressAPI
from app.models.address import AddressAPI
from app.models.role import Role
from app.models.address import Address, AddressSchema
from app.models.phone_number import PhoneNumber
from app.models.extensions import BaseExtension
from app.models.app_group import user_app_group, AppGroup, AppGroupSchema
from app.security import app_permission_useractivation, app_permission_userforceconfirmation, \
    app_permission_userpasswordchange, app_permission_userrolechange, app_permission_userappgroupupdate
from app.utils.demographics import *
from app.utils.general import json_serial, url_for


##################################################################################################
# SQL ALCHEMY USER MODEL DEFINITION
##################################################################################################

class User(UserMixin, sa.Model):
    # UserMixin from flask_login
    # is_authenticated() - Returns True if user has login credentials, else False
    # is_active() - Returns True if useris allowed to login, else False.
    # is_anonymous() - Returns False for logged in users
    # get_id() - Returns unique identifier for user, as Unicode string

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
        Represents User model instance as a string"""
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
        """Email is read only"""
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
        """Phone Number is ready only"""
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
        """Address is read only"""
        raise AttributeError('This property is read-only.')

    ####################################
    # RESOURCE URL BUILDER
    ####################################
    def get_url(self):
        """
        Helper method to build the api url of the user resource
        :return:
            Returns the absolute URL of the User resource in the User api.
        """
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

    def is_accessible(self, requesting_user, other_permissions=[], self_permissions=[]):
        __doc__ = """
        User Method:
        Helper function that checks whether the base user object should be
        accessible to another user attempting to perform operations on the record.
        
        Essentially answers, should the 'requesting_user' have access to this user object?

        The method first checks whether the identity of the user passed in the 'requesting_user' parameter matches the 
         supplied identity in the param requesting user.  This is usually the identify supplied by the session 
         cookie for logged in users, or the request after API auth.  
        If the identities match, the method then checks the param <self_permissions> for a list of Flask-Principal 
        permission objects that are required to be supplied by the requesting user to perform operations on their own 
        user record. If the requesting user object has all of the permissions listed in the param <self_permissions>, 
        as tested by performing <self_permission>.can(), the requesting user is determined to have access to perform 
        the given operation on their own user object and the method returns True.  If the param <self_permissions> 
        is None, the method will also return True.

        If the base user object does not match the identify of the requesting user, the list of permissions supplied 
        in the param <other_permissions> is checked against the current user identity.  If the requesting user object 
        has all of the permissions listed in the param <other_permissions>, as tested by performing 
        <other_permission>.can(),the requesting user is determined to have access to perform the given operation on 
        the base user object and the method returns True.  If the param <other_permissions> is None, the method
        will also return True.
        
        In all cases, the Role security levels are compared between the base user object and the requesting user.
        If the requesting user's Role.level <= the base user object, permission will be denied and False is 
        returned by the function, regardless of the application permissions provided by the user.

        param <user>:
            Either the integer user id of the user to be compared to the base user object, or the fully
            qualified user object to be compared with the base user.  If an integer input is detected, the
            user with that corresponding id is looked up in the database.  Otherwise, a fully qualified user
            object is assumed.


        param <self_permissions>:
            A list of Flask-Principal permission objects that must be provided by the requesting user in order
            to perform the protected user operation on the self-same user object.  If the list is set to None, no
            additional permissions are required.

            Default is: None

        param <other_permissions>:
            A list of Flask-Principal permission objects that must be provided by the requesting user in order
            to perform the protected user operation on the user specified in the param <user>.
            If the list is set to None, no additional permissions are required.

            Default is: None
            
        Returns:
            True if requesting user has access to base user & operation
            Fals if requestins user does not have access to base user & operation

        """
        if requesting_user:
            if isinstance(requesting_user, int):
                requesting_user = User.query.get(requesting_user)
                if not requesting_user:
                    raise ValueError("User could not be found.")
        else:
            if current_user and not current_user.is_anonymous():
                requesting_user = current_user
            elif g.current_user:
                requesting_user = current_user
            else:
                raise ValueError("No user was supplied and no logged in user was detected.")

        # Stuff to check is user is accessing their own record
        if self.id == requesting_user.id:
            # If self_permissions param is set, make sure all of those permissions are allowed
            if self_permissions:
                for perm in self_permissions:
                    if not perm.can():
                        return False
        # Stuff to check is user is accessing another user
        else:
            # Check for overlap between app groups.  If no shared group, deny access
            if not (set(self.app_groups) & set(requesting_user.app_groups)):
                return False
            if not requesting_user.has_higher_permission(user=self):
                return False
            if other_permissions:
                for perm in other_permissions:
                    if not perm.can():
                        return False
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
        self.app_groups.append(AppGroup.query.filter(AppGroup.default == True).first())
        test_pw = os.environ.get('TEST_USER_PASSWORD', None)
        if not test_pw:
            test_pw = demo_dict.get('password', None)
            if test_pw:
                test_pw = str(test_pw)
        self.password = test_pw

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
    """
    A helper function to be called to hash all Unknani passwords.  Employs pbkdf2:sha1 hashing with a
    salt length of 9 by default.
    :param password:
        Type: Str
        Contents: The password to be hashed
    :return:
        Returns sha1 hash of password string
    """
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
        n_username = normalize_username(username=username)
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


##################################################################################################
# USER API INTERFACE - MEDIATOR OBJECT FOR USER API
##################################################################################################
class UserAPI:
    """
    UserAPI:  An object class that mediates all operations on Unkani User objects.  May be used in
    conjunction with the Unkani API or within view functions of the Unkani App.

    Core Uses:
        1) De-serialize JSON representations of Users to SQLAlchemy.orm User model objects.
        2) Apply normalization and validation logic to User demographic attributes
        3) Update existing or create new SQLAlchemy.orm User model objects with normalized
            and validated data.

    Example Usage With Existing User Object:

        existing_user = User.query.get_or_404(<someuserid>)

        api = UserAPI()
        api._user = existing_user

        api.email = 'somenewemail@example.com'
        api.address = {'address1':'123 Main St',
                        'address2':'apt 101',
                        'city':'anytown', 'state':'wi',
                        'zipcode':'99999'}

        api.run_validations()
        if not api.errors['critical']:
            updated_user, errors = api.make_object()

            if updated_user:
                sa.session.add(updated_user)

    Example Usage With HTTP Request & JSON Payload for New User

        @some_api.route('users/', methods=['POST']
        def register_user():
            api = UserAPI()
            api.loads_json(request.get_json())
            api.run_validations()
            if not api.errors['critical']:
                user, errors = api.make_object()
                sa.session.add(user)
                response = jsonify({'user':user, 'errors': errors}
                return response
            else:
                response = jsonify({'user':user, 'errors':'Critical error during data validation.'})
                response.status_code = 400
                return response

    """

    def __init__(self, user=None, first_name=None, last_name=None, username=None, dob=None, sex=None, email=None,
                 description=None, active=None, confirmed=None, password=None, role_id=None, app_groups=None,
                 phone_number=None, address=None):
        self.errors = {"critical": {},
                       "warning": {}}
        self._user = user
        self._validation_complete = False

        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.dob = dob
        self.sex = sex
        self.email = email
        self.description = description
        self.active = active
        self.confirmed = confirmed
        self.password = password
        self.role_id = role_id
        self.app_groups = app_groups
        self.phone_number = phone_number
        self.address = address

    @property
    def user(self):
        """
        Accesses the protected class attribute '_user'
        :return:
            If '_user' exists, returns a SQLAlchemy ORM User type object instance
            Else returns None
        """
        if self._user:
            return self._user
        else:
            return None

    @user.setter
    def user(self, user):
        """
        Setter method for the protected class attribute '_user'
        Holds an existing User object to be updated (in application or with PUT/PATCH requests from API)
        If new User object is created with method self.make_object(), holds the newly created User object.

        :param user:
            type: SQLAlchemy ORM User object instance
        :return:
            If type requirements of param:user are not met, raises TypeError
            No return (setter method)
        """
        if user is None:
            pass
        elif isinstance(user, User):
            self._user = user
        else:
            raise TypeError('Object assigned to user was not a SQL Alchemy User type object.')

    def loads_json(self, data):
        """
        Used to load JSON formatted user data, or native python dict object.  Parses all data from the
        source and stores in class instances corresponding attributes.  These attributes are validated, normalized
        and ultimately dumped with other methods such as: self.run_validations() and self.make_object()

        :param data:
            type:
                JSON encoded string with valid User object key-value pairs (from User API).
                OR
                Native python dict with valid User object key-value pairs
        :return:
            Nothing
        """

        ud = None
        if isinstance(data, dict):  # Handle native python dicts
            ud = data
        else:
            try:
                ud = json.loads(data)  # Try loading JSON encoded string
            except json.decoder.JSONDecodeError as e:  # Handle JSON decode error.  Store in error dict
                self.errors['critical'][
                    'json decode error'] = 'An error occurred when attempting to decode JSON: {}'.format(e.args[0])
        if ud:  # Unpack user attributes and store in corresponding class attributes
            self.first_name = ud.get('first_name', None)
            self.last_name = ud.get('last_name', None)
            self.username = ud.get('username', None)
            self.dob = ud.get('dob', None)
            self.sex = ud.get('sex', None)
            self.email = ud.get('email', None)
            self.description = ud.get('description', None)
            self.active = ud.get('active', None)
            self.confirmed = ud.get('confirmed', None)
            self.password = ud.get('password', None)
            self.role_id = ud.get('role_id', None)
            self.phone_number = ud.get('phone_number', None)

            self.address = ud.get('address', {})
            self.app_groups = ud.get('app_groups', [])

    def validate_first_name(self):
        """
        Validation method for self.first_name
        Normalizes the case of the supplied first name and trims white space
        :return:
            Updates self.first_name
        """
        if self.first_name:
            self.first_name = normalize_name(name=self.first_name)
        else:
            self.first_name = None

    def validate_last_name(self):
        """
        Validation method for last name
        Normalizes the case of the supplied first name and trims white space
        :return:
            Updates self.last_name
        """
        if self.last_name:
            self.last_name = normalize_name(self.last_name)

        else:
            self.last_name = None

    def validate_dob(self):
        """
        Validation method for self.dob
        Uses dateutils datetime parser to handle any format of dates.
        :return:
            If self.dob exists and can be validated as a date, sets self.dob as a datetime.date type object
            If self.dob cannot be parsed into a valid date, sets self.dob to None and logs a critical error
                under the key 'dob' with detailed information about the error.
        """
        if self.dob:
            try:
                self.dob = validate_dob(self.dob)
            except ValueError as e:
                self.errors['warning']['dob'] = e.args[0]
                self.dob = None

    def validate_sex(self):
        """
        Validation method for self.sex
        Uses the Unkani validate_sex demographic utility to normalize biological sex representations to the
            approved set of string values, namely: 'MALE', 'FEMALE', 'OTHER', 'UNKNOWN'
        :return:
            If self.sex is a valid sex representation, self.sex is set with the approved sex string (see above)
            If self.sex is a forbidden value, self.sex is set to None and an error is logged to self.errors['warning']
        """
        if self.sex:
            try:
                self.sex = validate_sex(self.sex)
            except ValueError as e:
                self.errors['warning']['sex'] = e.args[0]
                self.sex = None

    def validate_username(self):
        """
        Validation method for self.username
        :return:
            Performs an upper and trim on the username provided and sets resulting value to self.username
            If no username is set, and no existing User object is assigned to self.user before validation is run,
            a critical error is logged to self.errors as a username is required for User creation.

            The validator also ensures that user.username remains unique within the database.  Any conflicts for
            newly registered users, or updated users will be logged as critical errors.
        """
        if isinstance(self.username, str):
            n_username = normalize_username(username=self.username)
            if self.user:  # Handle username lookup in case of existing user
                user_w_username = lookup_user_by_username(n_username)
                if user_w_username:
                    if self.user != user_w_username:
                        self.errors['critical']['username'] = 'The username {} is already registered. Could not change' \
                                                              ' the username.'.format(self.username)
                        self.username = None
                    else:
                        self.username = n_username
                else:
                    self.username = n_username

            else:
                if lookup_user_by_username(self.username):
                    self.errors['critical']['username'] = 'The username {} is already registered. Could not create' \
                                                          'new user account.'.format(self.username)
                    self.username = None
                else:
                    self.username = n_username

        elif not self.user:  # A username must be provided for account creation
            self.errors['critical']['username'] = 'A username string was not provided.  A username is required.'
            self.username = None

    def validate_description(self):
        """
        Validation method for self.description
        :return:
            If self.description is a string, the value is kept assigned to the class attribute.
            If any other data type, self.description is set to None and a warning is logged to self.errors
        """
        if self.description:
            if isinstance(self.description, str):
                pass
            else:
                self.description = None
                self.errors['warning']['description'] = 'A non-string value was supplied for the user description.'

    def validate_active(self):
        """
        Validation method for self.active
        :return:
            If self.active is a boolean value, the value is allowed
            Else, the value is set to None
        """
        if isinstance(self.active, bool):
            pass
        elif self.active:
            self.active = None
            self.errors['warning']['active'] = 'A non-null non-boolean value was supplied to the active attribute.'
        else:
            self.active = None

    def validate_confirmed(self):
        """
        Validation method for self.confirmed
        :return:
            If self.confirmed is a boolean value, the value is allowed
            Else, the value is set to None
        """
        if isinstance(self.confirmed, bool):
            self.confirmed = self.confirmed
        elif self.confirmed:
            self.confirmed = None
            self.errors['warning']['active'] = 'A non-null non-boolean value was supplied to the confirmed attribute.'
        else:
            self.confirmed = None

    def validate_password(self):
        """
        Validation method for password
        :return:
            If a password string is provided, does nothing
            If a pssword string is not provided and a user object does not exist before validations are run, a
                critical error is logged to self.errors as a password is required for user registration
        """
        if isinstance(self.password, str):
            pass
        elif not self.user:
            self.errors['critical']['password'] = 'A password was not provided.  A password is required for new users.'
            self.password = None
        else:
            self.password = None

    def validate_role_id(self):
        """
        Validation method for self.role_id

        :return:
            If self.role_id is set, validates that the role_id is an integer value and matches a Role record in the
                database.
            If self.role_id is set, and the validation fails, a warning is logged to self.errors.  In the case of
                existing users, the existing role will be left unchanged.  In the case of new users, the Role
                object will be initialized with the default role: 'User'
        """
        if self.role_id:
            roles = Role.query.all()
            role_ids = []
            for role in roles:
                role_ids.append(role.id)
            if self.role_id not in role_ids:
                self.role_id = None
                self.errors['warning']['role'] = 'An invalid id was passed as a role_id: {}'.format(self.role_id)

    def validate_app_groups(self):
        ids = set()
        bad_ids = set()
        if self.app_groups:
            if isinstance(self.app_groups, int):
                ids.add(self.app_groups)
            elif isinstance(self.app_groups, list):
                for i in self.app_groups:
                    if isinstance(i, int):
                        ids.add(i)
                    else:
                        bad_ids.add(i)
            else:
                self.app_groups = None
                self.errors['warning']['app_group_id'][
                    'type error'] = 'A non integer or non-string value was supplied as ' \
                                    'the app_group_id'

        if ids:
            valid_app_groups = []
            for id in ids:
                existing = AppGroup.query.get(id)
                print('Existing app group matched')
                print(existing)
                if not existing:
                    print('Existing not found')
                    bad_ids.add(id)
                else:
                    valid_app_groups.append(existing)
                    print('Appended app group to valid app agroups')
                    print(valid_app_groups)
            if bad_ids:
                for id in bad_ids:
                    ids.discard(id)
                self.errors['warning']['bad app group ids'] = 'Some app group ids were supplied that could not match ' \
                                                              'any app groups in the system.  They were ignored.  {}'.format(
                    bad_ids)
            if valid_app_groups:
                if not self.user:
                    self.app_groups = valid_app_groups
                else:
                    new_app_groups = []
                    for ag in valid_app_groups:
                        if ag not in self.user.app_groups:
                            new_app_groups.append(ag)
                    self.app_groups = new_app_groups

            else:
                self.app_groups = None

        if not self.app_groups and not self.user:
            if getattr(g, 'current_user', None):
                print('Current user found')
                if len(g.current_user.app_groups) == 1:
                    self.app_groups = g.current_user.app_groups
            if not self.app_groups:
                print('Setting default app group now instead')
                self.app_groups = [AppGroup.query.filter(AppGroup.default == True).first()]
                self.errors['warning']['app group missing'] = 'No valid app group id was supplied.  ' \
                                                              'The default was assigned: {}'.format(
                    self.app_groups[0].name)

    # Validate email, set self.email to EmailAddress object if valid, None if not.  Process errors to self.errors
    def validate_email(self):
        """
        Validation method for self.email

        :return:
            If self.email is not set and self.user is not set before validations are run, a critical error is logged
                as an email is required for user account creation.
            If self.email is set, and a valid email can be constructed from the string value, the upper-ed and
                trimmed email will be assigned to a SQLAlchemy ORM EmailAddress object and that object will
                be assigned to self.email
            If self.email is set, and an invalid email is provided, self.email is set to None and the errors
                from the validation function are logged to self.errors.  These may either be critical or warning.

            The validator also ensures that user.email remains unique within the database.  Any conflicts for
            newly registered users, or updated users will be logged as critical errors.
        """
        if self.email:
            # Initialize the EmailAddressAPI object and run email object validation and creation methods
            api = EmailAddressAPI(email=self.email, primary=True, active=True)
            api.run_validations()
            email_object, errors = api.make_object()

            # If email object cannot be created, process the EmailAddressAPI Errors
            if not email_object:
                self.email = None
                if not self.user:
                    self.errors['critical']['email taken'] = 'A valid email was not provided during user creation.  ' \
                                                             'This is required for account creation.'

            else:
                email_object.primary = True
                email_object.active = True
                if self.user:
                    user_w_email = lookup_user_by_email(email_object.email)
                    if user_w_email:
                        if user_w_email == self.user:
                            self.email = email_object
                        else:
                            self.email = None
                            self.errors['critical'][
                                'email taken'] = 'The email {} is already registered.  The email was not updated.'.format(
                                email_object.email)
                else:
                    # For new users, check for existence of email in database
                    if lookup_user_by_email(email_object.email):
                        self.errors['critical']['email taken'] = 'The email {} is already registered.'.format(
                            email_object.email)
                        self.email = None
                    else:
                        self.email = email_object

            # Surface errors from EmailAddressAPI and log to error dict of UserAPI
            if errors['critical']:
                if not getattr(self.errors['critical'], 'email', None):
                    self.errors['critical']['email'] = {}
                for key in errors['critical']:
                    self.errors['critical']['email'][key] = errors['critical'][key]

            if errors['warning']:
                if not getattr(self.errors['warning'], 'email', None):
                    self.errors['warning']['email'] = {}
                for key in errors['warning']:
                    self.errors['warning']['email'][key] = errors['warning'][key]

    # Validate phone, set self.phone_number to PhoneNumber object if valid, None if not.  Process errors to self.errors
    def validate_phone_number(self):
        """
       Validation method for self.phone_nmber

        :return:
            If self.phone_number is set, and a valid phone number can be constructed from the string value,
                the numeric digits of the phone number will be assigned to a SQLAlchemy ORM PhoneNumber object
                and that object will be assigned to self.phone_number
            If self.phone_number is set, and an invalid number is provided, self.phone_number is set to None
                and the errors from the validation function are logged to self.errors.
            A phone number is not required for user account creation or update.
        """
        if self.phone_number:
            # Initialize the PhoneNumberAPI.  Run validations and make the object.
            pn = PhoneNumberAPI(number=self.phone_number, type='MOBILE', active=True, primary=True)
            pn.run_validations()
            phone_number, errors = pn.make_object()

            # If phone number object cannot be created, process the PhoneNumberAPI Errors
            if not phone_number:
                self.phone_number = None
            elif isinstance(phone_number, PhoneNumber):
                phone_number.active = True
                phone_number.primary = True
                self.phone_number = phone_number

            # Surface errors from PhoneNumberAPI and log to error dict of UserAPI
            if errors['critical']:
                if not getattr(self.errors['warning'], 'phone_number', None):
                    self.errors['warning']['phone_number'] = {}
                for key in errors['critical']:
                    self.errors['warning']['phone_number'][key] = errors['critical'][key]

            if errors['warning']:
                if not getattr(self.errors['warning'], 'phone_number', None):
                    self.errors['warning']['phone_number'] = {}
                for key in errors['warning']:
                    self.errors['warning']['phone_number'][key] = errors['warning'][key]

    def validate_address(self):
        """
        Validation method for self.address

        :return:
            Attempts to unpack a valid address dictionary with keys: address1, address2, city, state and zipcode.
            If a dict cannot be unpacked from a non-null value, self.address is set to None and an error is logged.
            If a dict gets unpacked, the AddressAPI is invoked to create a SQLAlchemy ORM Address object.  If the
                object is successfully created, it is assigned to self.address.  If an object cannot be created,
                self.address is set to None.  All errors from the AddressAPI are logged under the self.errors
                dictionary as warnings.
            Note: An address is NOT required to create / update an account.
        """
        if self.address:
            if not isinstance(self.address, dict):
                self.errors['warning']['address']['invalid_format'] = 'Address information was not supplied as' \
                                                                      ' a dictionary of key value pairs.  The address' \
                                                                      ' for the user could not be set.'
                self.address = None
            else:
                addr_dict = dict(self.address)

                address1 = addr_dict.get('address1', None)
                address2 = addr_dict.get('address2', None)
                city = addr_dict.get('city', None)
                state = addr_dict.get('state', None)
                zipcode = addr_dict.get('zipcode', None)
                primary = addr_dict.get('primary', False)
                active = addr_dict.get('active', True)

                api = AddressAPI(address1=address1, address2=address2, city=city, state=state, zipcode=zipcode,
                                 active=active, primary=primary)
                api.run_validations()
                a, errors = api.make_object()

                if not a:
                    self.errors['warning']['address'][
                        'address_creation'] = 'Unable to create an address from the supplied data.'
                    self.address = None

                if isinstance(a, Address):
                    if errors['critical'] or errors['warning']:
                        if errors['critical']:
                            for key in errors['critical']:
                                self.errors['warning']['address'][key] = errors['critical'][key]
                        if errors['warning']:
                            for key in errors['warning']:
                                self.errors['warning']['address'][key] = errors['warning'][key]

                    a.primary = True
                    a.active = True

                    self.address = a

    def permission_check_active(self):
        """
        Permission check for user.active.
        :return:
            If self.active is set to a boolean value, the requesting authenticated user must have the app-permission
                'user activation'.  If permission check fails, self.active is set to None and an warning is logged
                to self.errors
        """
        if isinstance(self.active, bool):
            if not app_permission_useractivation.can():
                self.active = None
                self.errors['warning']['permission: user deactivate'] = 'Could not set user activation. ' \
                                                                        'Permission denied. User must be activated or' \
                                                                        ' deactivated by an admin.'

    def permission_check_confirmed(self):
        """
        Permission check for user.confirmed.
        :return:
            If self.confirmed is set to a boolean value, the requesting authenticated user must have the app-permission
                'user force confirmation'.  If permission check fails, self.confirmed is set to None and an warning is
                logged to self.errors
        """
        if isinstance(self.confirmed, bool):
            # Verify permission to force set User.confirmed
            if not app_permission_userforceconfirmation.can():
                # Set to None.  Will not be written to user object during de-serialization
                self.confirmed = None
                self.errors['warning']['permission: force confirm'] = 'Attempt to force set confirmation failed.' \
                                                                      ' Permission not granted to user.'

    def permission_check_password(self):
        """
        Permission check for user.password

        :return:
            If a user object already exists (is being updated) and self.password passes validation, the user must
                have the app-permission 'user password change'.  If permission check fails, self.password is set
                to None and a warning is logged.  The password will not be changed.
        """
        if self.user and self.password:
            if not app_permission_userpasswordchange.can():
                self.password = None
                self.errors['warning']['password'] = 'Insufficient permissions to update another users password.'

    def permission_check_role_id(self):
        """
        Permission check method for self.role_id
        :return:
            If self.role id is supplied and passes validation, the user must have the app-permission
                'user role change'.  If this check passes, the target role's security level must also be lower
                than that of the requesting authenticated user.
            If permission check fails, self.role_id is set to None and either the existing
                or default role will be assigned to the object for existing and new users, respectively.
        """
        if self.role_id:
            if not app_permission_userrolechange.can():
                self.role_id = None
                self.errors['warning']['role'] = 'Failed setting role_id for user due to insufficient permissions.'
            if Role.query.get(self.role_id).level > g.current_user.role.level:
                self.role_id = None
                self.errors['warning']['role'] = 'Could not set role to a role with a higher permission' \
                                                 ' level than the requesting user.'

    def permission_check_app_groups(self):
        if self.app_groups:
            if not app_permission_userappgroupupdate.can():
                if self.user:
                    self.app_groups = None
                    self.errors['warning']['app group permission'] = 'The authenticated user does not have access' \
                                                                     ' to assign app groups.  The existing users ' \
                                                                     'app group was not updated.'
                else:
                    self.app_groups = [AppGroup.query.filter(AppGroup.default == True).first()]
                    self.errors['warning']['app group permission'] = 'The authenticated user does not have access' \
                                                                     ' to assign app groups.  The default app group' \
                                                                     ' was assigned to the new user.'
            elif g.current_user:
                restricted_ags = []
                for ag in self.app_groups:
                    if ag not in g.current_user.app_groups and self.app_groups != AppGroup.query.filter(
                                    AppGroup.default == True).first():
                        restricted_ags.append(ag)
                    if restricted_ags:
                        for ag in restricted_ags:
                            self.app_groups.pop(ag)
                    if not self.app_groups:
                        if self.user:
                            self.app_groups = None
                            self.errors['warning'][
                                'app group membership'] = 'Authenticated user attempted to assign the' \
                                                          ' existing user to one or more app groups ' \
                                                          'of which the authenicated user is not a member.  The ' \
                                                          'existing app group was retained.  Bad app groups: {}'.format(
                                restricted_ags)
                        else:
                            self.errors['critical'][
                                'app group membership'] = 'Authenticated user attempted to assign the' \
                                                          ' new user to an app group that they do not' \
                                                          'have access to. {}'.format(restricted_ags)
                            self.app_groups = None

    def run_validations(self):
        """
        Convenience method to run all validations.
        """
        self.validate_first_name()
        self.validate_last_name()
        self.validate_dob()
        self.validate_sex()
        self.validate_username()
        self.validate_confirmed()  # Must run after email
        self.validate_email()
        self.validate_phone_number()
        self.validate_active()
        self.validate_description()
        self.validate_password()
        self.validate_role_id()
        self.validate_address()
        self.validate_app_groups()
        self._validation_complete = True

    def run_permission_checks(self):
        """Convenience method to run all permission checks."""
        self.permission_check_active()
        self.permission_check_confirmed()
        self.permission_check_role_id()
        self.permission_check_password()
        self.permission_check_app_groups()

    def make_object(self):
        """
        Method to process post-validated UserAPI object.
        Requires self.run_validations() to be called before running.
        :return:
            If critical errors are logged, returns the tuple (None, self.errors)
            If self.run_validations() has not been completed, returns the tuple (None, self.errors)
            If validations passed and an existing user is logged to self.user, returns the tuple (user, self.errors)
                where user is the existing and now updated user object and self.errors is the error dictionary.
            If no user exists and is assigned to self.users, creates a new user object and returns it in the tuple
                (user, errors)

        """
        # Any critical errors?  Do not make the object.
        if self.errors['critical']:
            return None, self.errors

        # If validation did not run, do not make the object.
        elif not self._validation_complete:
            raise ValidationError('Validations must be completed before object is created or updated.')

        # Do the dirty work of creating the user now
        else:
            if isinstance(self.user, User):  # Get existing user
                u = self.user
            else:  # Or initialize new user
                u = User()

            if self.role_id:
                u.role_id = self.role_id
            if self.first_name:
                u.first_name = self.first_name
            if self.last_name:
                u.last_name = self.last_name
            if self.dob:
                u.dob = self.dob
            if self.sex:
                u.sex = self.sex
            if self.username:
                u.username = self.username
            if isinstance(self.email, EmailAddress):
                update_existing = False
                existing_addresses = u.email_addresses.all()
                if existing_addresses:
                    existing_primary_address = u.email
                    if self.email.email == existing_primary_address.email:
                        update_existing = True
                    else:
                        existing_primary_address.primary = False
                        existing_primary_address.active = False
                        for a in existing_addresses:
                            if a == existing_primary_address:
                                pass
                            elif self.email.email == a.email:
                                a.primary = True
                                a.active = True
                                update_existing = True
                if update_existing:
                    self.email = None

                if self.email:

                    u.email_addresses.append(self.email)

                    if not isinstance(self.confirmed, bool):
                        self.confirmed = False
                    if self.user and not self.confirmed:
                        self.errors['warning']['account_confirmation'] = 'Email address has been changed.  The' \
                                                                         ' account requires confirmation.'
                        token = u.generate_email_change_token(self.email.email.lower())
                        send_email(subject='Unkani - Email Change', to=[self.email.email.lower()],
                                   template='auth/email/change_email',
                                   token=token, user=self.user)

            if isinstance(self.phone_number, PhoneNumber):
                update_existing = False
                existing_addresses = u.phone_numbers.all()
                if existing_addresses:
                    existing_primary_address = u.phone_number
                    if self.phone_number.number == existing_primary_address.number:
                        update_existing = True
                    else:
                        existing_primary_address.primary = False
                        existing_primary_address.active = False
                        for a in existing_addresses:
                            if a == existing_primary_address:
                                pass
                            elif self.phone_number.number == a.number:
                                a.primary = True
                                a.active = True
                                update_existing = True
                if update_existing:
                    self.phone_number = None

                if self.phone_number:
                    u.phone_numbers.append(self.phone_number)

            if self.description:
                u.description = self.description

            # Set password if validation and permission passes
            if self.password:
                u.password = self.password

            # Set active is validation and permission passes
            if isinstance(self.active, bool):
                u.active = self.active

            # Set confirmation if True / False is set and permissions are in place
            if isinstance(self.confirmed, bool):
                u.confirmed = self.confirmed

            if isinstance(self.address, Address):
                update_existing = False
                existing_addresses = u.addresses.all()
                if existing_addresses:
                    existing_primary_address = u.address
                    new_address_hash = self.address.generate_address_hash()
                    if new_address_hash == existing_primary_address.address_hash:
                        update_existing = True
                    else:
                        existing_primary_address.primary = False
                        existing_primary_address.active = False
                        for a in existing_addresses:
                            if a == existing_primary_address:
                                pass
                            elif new_address_hash == a.address_hash:
                                a.primary = True
                                a.active = True
                                update_existing = True
                if update_existing:
                    self.address = None

                if self.address:
                    u.addresses.append(self.address)

                if self.app_groups:
                    for ag in self.app_groups:
                        u.app_groups.append(ag)

            self.user = u

            return self.user, self.errors
