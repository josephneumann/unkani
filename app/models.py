from flask import current_app, request

from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime, date
from random import randint, choice
from names import get_first_name, get_last_name
import os
import re
import hashlib

role_app_permission = db.Table('role_app_permission',
                               db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                               db.Column('app_permission_id', db.Integer, db.ForeignKey('app_permission.id'))
                               )


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
        roles = {
            'Admin': ('1'),
            'User': ('2'),
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
                role.id = int(roles[r][0])
                if role.name == 'User':
                    role.default = True
                db.session.add(role)
        db.session.commit()


class AppPermission(db.Model):
    __tablename__ = 'app_permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return str(self.id)

    @staticmethod
    def initialize_app_permissions():
        app_permissions = {
            'Admin': (1),
            'User Create': (2),
            'User Delete': (3),
            'User Update': (4),
            'User View': (5),
            'Role Create': (6),
            'Role Delete': (7),
            'Role Update': (8),
            'Role View': (9),
            'App Permission Create': (10),
            'App Permission Delete': (11),
            'App Permission Update': (12),
            'App Permission View': (13),
        }
        for p in app_permissions:
            app_permission = AppPermission.query.filter_by(name=p).first()
            if app_permission is None:
                app_permission = AppPermission(name=p)
                app_permission.id = app_permissions[p]
                db.session.add(app_permission)
        db.session.commit()


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
        if self.email is not None and self.avatar_hash is None:
            if not re.search(r'(@example.com)+', self.email):
                self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        self.active = True
        self.confirmed = False

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

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
        if not re.search(r'(@example.com)+', new_email):
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
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

    def create_random_user(self, gender=None, **kwargs):
        allowed_genders = ['male', 'female']
        if gender:
            if gender not in allowed_genders:
                gender = None

        email_domains = ['@gmail.com', '@icloud.com', '@yahoo.com', '@microsoft.com'
            , '@aol.com', '@comcast.com', '@mail.com', '@inbox.com', '@outlook.com']
        email_domains_number = len(email_domains)
        random_number = str(randint(0, 1000))
        rand_email_index = randint(0, (email_domains_number - 1))
        self.first_name = get_first_name(gender)
        self.last_name = get_last_name()
        self.username = self.first_name + '.' + self.last_name + random_number
        rand_domain = email_domains[rand_email_index]
        self.email = self.username + rand_domain
        self.dob = self.random_dob()
        self.phone = self.random_phone()
        password = kwargs.get('password')
        if not password:
            password = os.environ.get('TEST_USER_PASSWORD')
        self.password = password
        self.avatar_hash = self.gravatar()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)


# Callback function, receives a user identifier and returns either user object or None
# used by Flask-Login to set current_user()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
