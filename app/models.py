from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import login_manager



class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    patient = db.relationship('Patient', backref='user', uselist=False)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError ('Password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password,method='pbkdf2:sha1',salt_length=8)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(128), nullable=False, index=True)
    last_name = db.Column(db.String(128), nullable=False, index=True)
    middle_initial = db.Column(db.String(1), nullable=True)
    dob = db.Column(db.Date,nullable=False, index=True)
    gender = db.Column(db.String(1), nullable=True)
    address1 = db.Column(db.String(256), nullable=True)
    address2 = db.Column(db.String(256), nullable=True)
    city = db.Column(db.String(128), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zip = db.Column(db.String(9), nullable=True)
    ssn = db.Column(db.String(9), nullable=True, index=True)
    phone_mobile = db.Column(db.String(16), nullable=True, index=True)
    phone_home = db.Column(db.String(16), nullable=True)
    email = db.Column(db.String(64), nullable=True, index=True)

    def __repr__(self):
        return '<Patient %r>' % self.id

#Callback function, receives a user identifier and returns either user object or None
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))