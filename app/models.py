import hashlib
import os
import re
from datetime import datetime, date
from random import randint, choice
from app.security import *
from flask import current_app, request, url_for, g, abort, jsonify
from flask_login import UserMixin, AnonymousUserMixin
from marshmallow import fields, ValidationError, post_load, validates
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager, ma

##################################################################################################
# ROLE -> APP PERMISSION ASSOCIATION TABLE
##################################################################################################

role_app_permission = db.Table('role_app_permission',
                               db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                               db.Column('app_permission_id', db.Integer, db.ForeignKey('app_permission.id'))
                               )


###################################################################################################
# USER ROLE SQL ALCHEMY MODEL DEFINITION
###################################################################################################
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    default = db.Column(db.Boolean, default=False)
    level = db.Column(db.Integer)
    app_permissions = db.relationship('AppPermission',
                                      secondary=role_app_permission,
                                      backref=db.backref('app_permissions', lazy='dynamic'),
                                      lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def initialize_roles():
        __doc__ = """
        Role Staticmethod:  Creates and stores a default set of Roles as defined
        by the application security module.  Populates Role attributes including: 'id', 'name',
        'level'.  Also populates app_permissions in the role_app_permission association table
        to initialize the permissions for the given role."""
        from app.security import role_dict
        for r in role_dict:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r, id=role_dict[r]['id'], level=role_dict[r]['level'])
                if role.name == 'User':
                    role.default = True
                db.session.add(role)
                db.session.commit()
            role = Role.query.filter_by(name=r).first()
            for p in role_dict[r]['permissions']:
                ap = AppPermission.query.filter_by(name=p).first()
                if ap:
                    role_ap_list = role.app_permissions.all()
                    if ap not in role_ap_list:
                        role.app_permissions.append(ap)
            db.session.add(role)
            db.session.commit()

        db.session.commit()


###################################################################################################
# APP PERMISSION SQL ALCHEMY MODEL DEFINITION
###################################################################################################

class AppPermission(db.Model):
    __tablename__ = 'app_permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return str(self.name)

    @staticmethod
    def initialize_app_permissions():
        __doc__ = """
        AppPermission Staticmethod:  Initializes the set of AppPermission records as
        defined in the app security module.  Reads from a dict to assign names to permission.
        If app_permission already exists, it is ignored.  This method is used during deployment
        and on database creation / upgrades."""
        from app.security import app_permissions_dict
        for p in app_permissions_dict:
            app_permission = AppPermission.query.filter_by(name=p).first()
            if app_permission is None:
                app_permission = AppPermission(name=p)
                app_permission.id = app_permissions_dict[p]
                db.session.add(app_permission)
        db.session.commit()


##################################################################################################
# MARSHMALLOW USER SCHEMA DEFINITION FOR OBJECT SERIALIZATION AND INPUT VALIDATION
##################################################################################################

class UserSchema(ma.Schema):
    __doc__ = """
    Marshmallow schema, associated with SQLAlchemy User model.  Used as a base object for
    serialization and de-serialization.  Defines read-only and write only attributes for basic
    object use.  Defines validation criteria for input."""
    id = fields.Int(dump_only=True)
    email = fields.Email(dump_only=True)
    username = fields.String(dump_only=True)
    password = fields.String(load_only=True)
    first_name = fields.String()
    last_name = fields.String()
    dob = fields.Date()
    phone = fields.String()
    description = fields.String()
    confirmed = fields.Boolean(dump_only=True)
    active = fields.Boolean(dump_only=True)
    gravatar_url = fields.Method("generate_gravatar_url", dump_only=True)
    role_id = fields.Int(dump_only=True)
    role_name = fields.Method("get_role_name", dump_only=True)
    create_timestamp = fields.DateTime(dump_only=True)
    last_seen = fields.DateTime(dump_only=True)

    def generate_gravatar_url(self, user):
        __doc__ = """
        Calls gravatar method for user, and outputs a fully qualified gravatar URL."""
        return user.gravatar()

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


##################################################################################################
# SQL ALCHEMY USER MODEL DEFINITION
##################################################################################################

# UserMixin from flask_login
# is_authenticated() - Returns True if user has login credentials, else False
# is_active() - Returns True if useris allowed to login, else False.
# is_anonymous() - Returns False for logged in users
# get_id() - Returns unique identifier for user, as Unicode string
class User(UserMixin, db.Model):
    ##################################
    # MODEL ATTRIBUTES AND PROPERTIES
    ##################################
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, index=True)
    email = db.Column(db.String(128), unique=True, index=True)
    last_email = db.Column(db.String(128), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    password_hash = db.Column(db.String(128))
    last_password_hash = db.Column(db.String(128))
    password_timestamp = db.Column(db.TIMESTAMP)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    dob = db.Column(db.Date)
    phone = db.Column(db.String(16))
    description = db.Column(db.Text)
    confirmed = db.Column(db.Boolean, default=False)
    active = db.Column(db.BOOLEAN, default=True)
    create_timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow())
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(128))

    def __repr__(self):
        __doc__ = """
        Represents user model instance as a username string"""
        return '<User %r>' % self.username

    @property
    def dob_string(self):
        __doc__ = """
        Represent User's DOB as a string with format 'YYYY-MM-DD'"""
        if self.dob:
            return self.dob.strftime('%Y-%m-%d')
        else:
            return None

    @property
    def joined_year(self):
        __doc__ = """
        Represents the year the user record was created with format 'YYYY'"""
        if self.create_timestamp:
            return self.create_timestamp.strftime('%Y')
        else:
            return None

    #############################
    # USER OBJECT INITIALIZATION
    #############################
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['UNKANI_ADMIN']:
                self.role = Role.query.filter_by(name='Super Admin').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        self.generate_avatar_hash()
        self.active = True
        self.confirmed = False

    def ping(self):
        __doc__ = """
        Ping function called before each request initiated by authenticated user.
        Stores timestamp of last request for the user in the 'last_seen' attribute."""
        self.last_seen = datetime.utcnow()
        db.session.add(self)

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
        Defines setter method for property 'password'.  The sring passed as the password
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
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
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
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        __doc__ = """
        Generates a Timed JSON Web Signature encoding the user's id using the application
        SECRET KEY.  Also encodes a key-value pair for email change and validation."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_password': self.id, 'new_email': new_email})

    def change_email(self, token):
        __doc__ = """
        Decode and validate a Time JSON Web Signature supplied as the 'Token' variable. Ensure
        that the id encoded in the token matches the expected user.  Check for a 'change_password'
        key in the token with a value matching the current user id.  If match exists for specified
        user, update the user email with the email supplied in the token as 'new_email'."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_password') != self.id:
            return False
        new_email = data.get('new_email')
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.last_email = self.email
        self.email = new_email
        self.generate_avatar_hash()
        db.session.add(self)
        return True

    def verify_email(self, email):
        __doc__ = """
        Helper method to compare a supplied email with the user's email.  Returns True
        if email matches, False if not."""
        if self.email.lower() == email.lower():
            return True
        else:
            return False

    def verify_last_email(self, email):
        __doc__ = """
        Helper method to compare a supplied email with the user's last email.  Returns True
        if email matches, False if not."""
        if self.last_email.lower() == email.lower():
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
    def generate_avatar_hash(self):
        __doc__ = """
        Generate an MD5 hash of the user's email.  Stores the result in the user
        'avatar_hash' attribute.  This value is used when constructing the gravatar URL."""
        if self.email and not re.search(r'(@example.com)+', self.email):
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        __doc__ = """
        Generate a Gravatar url based on an MD5 hash of the user's email. URL output
        conforms to standards for Globally Recognized Avatar service.
        Defaults established as:
         Size: 100px
         Default: identicon (if gravatar not found, pattern unique to MD5 hash is displayed\
         Rating: g
         """
        url = 'https://secure.gravatar.com/avatar'
        if not self.avatar_hash:
            self.generate_avatar_hash()
            db.session.add(self)
            db.session.commit()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=self.avatar_hash, size=size, default=default, rating=rating)

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

    @staticmethod
    def random_dob():
        __doc__ = """
        Returns a random DOB as a datetime.date object."""
        current_datetime = datetime.now()
        year = choice(range(current_datetime.year - 100, current_datetime.year - 1))
        month = choice(range(1, 13))
        day = choice(range(1, 29))
        dob = date(year, month, day)
        return dob

    @staticmethod
    def random_phone():
        __doc__ = """
        Returns a random phone number as a string."""
        p = list('0000000000')
        p[0] = str(randint(1, 9))
        for i in [1, 2, 6, 7, 8]:
            p[i] = str(randint(0, 9))
        for i in [3, 4]:
            p[i] = str(randint(0, 8))
        if p[3] == p[4] == 0:
            p[5] = str(randint(1, 8))
        else:
            p[5] = str(randint(0, 8))
        n = range(10)
        if p[6] == p[7] == p[8]:
            n = [i for i in n if i != p[6]]
        p[9] = str(choice(n))
        p = ''.join(p)
        return str(p[:3] + '-' + p[3:6] + '-' + p[6:])

    @staticmethod
    def random_password():
        __doc__ = """
        Returns a random password as a string."""
        import forgery_py
        random_number = str(randint(0, 1000))
        password = forgery_py.lorem_ipsum.word() + random_number + forgery_py.lorem_ipsum.word()
        return password

    def randomize_user(self, **kwargs):
        __doc__ = """
        User Method: acts upon an initialized user object and randomizes key attributes
        of the user.

        Always Randomized: email, username, first_name, last_name, phone, dob

        Gender:  May be provided with a keyword argument for 'gender' with value of 'Male'
        or 'Female' provided exactly.  If gender is provided, a gender-specific first name
        is created.  If kwarg is not present, a name is generated that disregards gender.

        Password:  If a password is supplied in the environment variable 'TEST_USER_PASSWORD'
        that password is assigned to the user.  If not present, the password is randomized.
        """
        import forgery_py
        gender = kwargs.get('gender')
        allowed_genders = ['Male', 'Female']
        if not gender or gender not in allowed_genders:
            gender = forgery_py.personal.gender()

        email_domains = ['@gmail.com', '@icloud.com', '@yahoo.com', '@microsoft.com'
            , '@aol.com', '@comcast.com', '@mail.com', '@inbox.com', '@outlook.com']
        email_domains_number = len(email_domains)
        random_number = str(randint(0, 1000))
        rand_email_index = randint(0, (email_domains_number - 1))
        if gender == 'Male':
            self.first_name = forgery_py.name.male_first_name()
        if gender == 'Female':
            self.first_name = forgery_py.name.female_first_name()
        self.last_name = forgery_py.name.last_name()
        self.username = self.first_name + '.' + self.last_name + random_number
        rand_domain = email_domains[rand_email_index]
        self.email = self.username + rand_domain
        self.dob = self.random_dob()
        self.phone = self.random_phone()

        password = kwargs.get('password')
        if not password:
            password = os.environ.get('TEST_USER_PASSWORD')
            if not password:
                password = self.random_password()
        self.password = password
        self.gravatar()

    @staticmethod
    def initialize_admin_user():
        __doc__ = """
        User staticmethod: Generates and commits a super_admin user.  Loads user
        attributes stored as environment variables specified as 'UNKANI_ADMIN_*.
        Executed on deployment and db creation.  Checks for existing user with admin's
        email before attempting to create a new one."""
        admin_user_email = os.environ.get('UNKANI_ADMIN_EMAIL')
        user = User.query.filter_by(email=admin_user_email).first()
        if user is None:
            user = User(email=admin_user_email)
            user.username = os.environ.get('UNKANI_ADMIN_USERNAME')
            user.password = os.environ.get('UNKANI_ADMIN_PASSWORD')
            user.first_name = os.environ.get('UNKANI_ADMIN_FIRST_NAME')
            user.last_name = os.environ.get('UNKANI_ADMIN_LAST_NAME')
            user.phone = os.environ.get('UNKANI_ADMIN_PHONE')
            user.confirmed = True
            db.session.add(user)
            db.session.commit()


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
