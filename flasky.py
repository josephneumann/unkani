#flasky.py
import os
from threading import Thread
#from datetime import datetime
#from flask.ext.moment import Moment
from flask.ext.script import Manager
from flask import Flask, render_template, url_for, redirect, session, flash
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Shell
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail, Message
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


#basedir = os.path.abspath.dirname(__file__))

#Initialize flask app
app = Flask(__name__)

#Initialize config variables
app.config['SECRET_KEY'] ='hfwznel2805lkd43o98udnj'
app.config['SQLALCHEMY_DATABASE_URI']=\
    'postgresql://JosephNeumann:rascal60276@localhost:5432/flasky'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'FLasky Admin app.unkani.com'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')



#Initialize Flask Extensions
#moment = Moment(app)
manager = Manager(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

#Define ORM Models
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True, nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

#Define classes and helper functions
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email , args=[app,msg])
    thr.start()
    return thr


class NameForm(Form):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

def make_shell_context():
    return dict (app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


#Import Database and Models Automatically
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))

#Error handling with Flask functions
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#Flask URL Routing
@app.route('/', methods= ['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))

if __name__ == '__main__':
    db.create_all()
    #app.run(debug="True")
    manager.run()

