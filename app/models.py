import hashlib
import os
import re
from datetime import datetime, date
from random import randint, choice

from flask import current_app, request, url_for, g, abort, jsonify
from flask_login import UserMixin, AnonymousUserMixin
from marshmallow import fields, ValidationError, post_load, validates
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from app.security import app_permission_admin
from . import db, login_manager, ma

#######################################################################################################################
#                                     ROLE -> APP PERMISSION ASSOCIATION TABLE                                        #
#######################################################################################################################

role_app_permission = db.Table('role_app_permission',
                               db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                               db.Column('app_permission_id', db.Integer, db.ForeignKey('app_permission.id'))
                               )


#######################################################################################################################
#                                               ROLE MODEL DEFINITION                                                 #
#######################################################################################################################

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    default = db.Column(db.Boolean, default=False)
    app_permissions = db.relationship('AppPermission',
                                      secondary=role_app_permission,
                                      backref=db.backref('app_permissions', lazy='dynamic'),
                                      lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def initialize_roles():
        from app.security import role_dict
        for r in role_dict:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r, id=role_dict[r]['id'])
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


#######################################################################################################################
#                                     APP PERMISSION MODEL DEFINITION                                                 #
#######################################################################################################################

class AppPermission(db.Model):
    __tablename__ = 'app_permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    # TODO refactor and don't rely on this for other fucntionality
    def __repr__(self):
        return str(self.name)

    @staticmethod
    def initialize_app_permissions():
        from app.security import app_permissions_dict
        for p in app_permissions_dict:
            app_permission = AppPermission.query.filter_by(name=p).first()
            if app_permission is None:
                app_permission = AppPermission(name=p)
                app_permission.id = app_permissions_dict[p]
                db.session.add(app_permission)
        db.session.commit()


#######################################################################################################################
#                                               USER MODEL DEFINITION                                                 #
#######################################################################################################################

class UserSchema(ma.Schema):
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
        return user.gravatar()

    def get_role_name(self, user):
        return user.role.name


class UserSchemaCreate(UserSchema):
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
    id = fields.Int(required=True)
    email = fields.Email(dump_only=False)
    username = fields.String(dump_only=False)

    # @validates('email')
    # def validate_email(self, data):
    #     userid = data.get('id')
    #     email = data.get('email')
    #     user_with_email = User.query.get(userid).first()
    #     if email and user_with_email:
    #         if user_with_email.id != userid:
    #             raise ValidationError('An account with the email {} already exists.'.format(email))
    #
    # @validates('username')
    # def validate_username(self, data):
    #     userid = int(data['id'])
    #     username = data.get('username')
    #     user_with_username = User.query.get(userid).first()
    #     if username and user_with_username:
    #         if user_with_username.id != userid:
    #             raise ValidationError('An account with the username {} already exists.'.format(username))

    @post_load
    def update_user(self, data):
        return User(**data)


# UserMixin from flask_login
# is_authenticated() - Returns True if user has login credentials, else False
# is_active() - Returns True if useris allowed to login, else False.
# is_anonymous() - Returns False for logged in users
# get_id() - Returns unique identifier for user, as Unicode string
class User(UserMixin, db.Model):
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
        return '<User %r>' % self.username

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['UNKANI_ADMIN']:
                self.role = Role.query.filter_by(name='Admin').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        self.generate_avatar_hash()
        self.active = True
        self.confirmed = False

    def has_admin_permission(self):
        if app_permission_admin.can():
            return True
        else:
            return False

    def to_dict(self):
        dict_user = {"user": {
            'id': self.id,
            'url': url_for('api.get_user', id=self.id, _external=True),
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'dob': self.dob_string,
            'phone': self.phone,
            'role_id': self.role_id,
            'role_name': self.role.name,
            'gravatar_url': self.gravatar(),
            'confirmed': self.confirmed,
            'active': self.active,
            'create_timestamp': str(self.create_timestamp),
            'last_seen': str(self.last_seen)
        }}
        return dict_user

    @staticmethod
    def create(data):
        """Create a new user object from dict / json."""
        user = User()
        user.from_dict(data, update=False)
        return user

    @staticmethod
    def update(user, data):
        """Create a new user object from dict / json."""
        user.from_dict(data, update=True)
        return user

    def from_dict(self, data, update=False):
        """Import user data from a dict / json."""
        for field in ['username', 'password', 'email', 'first_name', 'last_name']:
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not update:
                    abort(400)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @property
    def dob_string(self):
        if self.dob:
            return self.dob.strftime('%Y-%m-%d')
        else:
            return None

    @property
    def joined_year(self):
        if self.create_timestamp:
            return self.create_timestamp.strftime('%b-%Y')
        else:
            return None

    @staticmethod
    def random_dob():
        current_datetime = datetime.now()
        year = choice(range(current_datetime.year - 100, current_datetime.year - 10))
        month = choice(range(1, 13))
        day = choice(range(1, 29))
        dob = date(year, month, day)
        return dob

    @staticmethod
    def random_phone():
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
        import forgery_py
        random_number = str(randint(0, 1000))
        password = forgery_py.lorem_ipsum.word() + random_number + forgery_py.lorem_ipsum.word()
        return password

    @password.setter
    def password(self, password):
        if self.password_hash:
            self.last_password_hash = self.password_hash
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha1', salt_length=8)
        self.password_timestamp = datetime.utcnow()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def verify_last_password(self, password):
        return check_password_hash(self.last_password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
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
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
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
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_password': self.id, 'new_email': new_email})

    def change_email(self, token):
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
        if self.email == email:
            return True
        else:
            return False

    def verify_last_email(self, email):
        if self.last_email == email:
            return True
        else:
            return False

    @staticmethod
    def initialize_admin_user():
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

    def randomize_user(self, **kwargs):
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

    def generate_avatar_hash(self):
        if self.email and not re.search(r'(@example.com)+', self.email):
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        if not self.avatar_hash:
            self.generate_avatar_hash()
            db.session.add(self)
            db.session.commit()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=self.avatar_hash, size=size, default=default, rating=rating)

    def generate_api_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({'id': self.id}).decode('ascii')
        return token

    @staticmethod
    def verify_api_auth_token(token):
        __doc__ = """
        User Method:  verify_api_auth_token takes a token and,
         if found valid, returns the user stored in it.
         """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(int(data['id']))


class AnonymousUser(AnonymousUserMixin):
    pass


login_manager.anonymous_user = AnonymousUser


# Callback function, receives a user identifier and returns either user object or None
# used by Flask-Login to set current_user()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_schema_create = UserSchemaCreate()
users_schema_create = UserSchemaCreate(many=True)
user_schema_update = UserSchemaUpdate()
users_schema_update = UserSchemaUpdate(many=True)
