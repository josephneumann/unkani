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

class Animal(db.Model):
    __tablename__ = 'animal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    family_name = db.Column(db.String(128))
    dob = db.Column(db.Date)
    species = db.Column(db.String(128))

    def __repr__(self):
        return '<Animal %r>' % self.id


#Callback function, receives a user identifier and returns either user object or None
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))