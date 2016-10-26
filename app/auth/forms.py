from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from .. models import User

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(),Length(1,128),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RegistrationForm(Form):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1,128)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1,128)])
    #dob=DateField('DOB', validators=[DataRequired])
    email = StringField('Email', validators=[DataRequired(),Length(1,128),Email()])
    #phone=StringField('phone', validators=None)
    username = StringField('Username', validators=[DataRequired(), Length(5,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', flags = 0, message = 'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password', validators=[DataRequired(),Length(10,128), EqualTo('password2', message = 'Passwords must match')])
    password2 = PasswordField('Confirm Password', validators = [DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(Form):
    old_password = PasswordField('Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(),Length(10,128), EqualTo('password2', message = 'Passwords must match')])
    password2 = PasswordField('Confirm New Password', validators = [DataRequired()])
    submit = SubmitField('Change Password')

class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 128), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 128), Email()])
    password = PasswordField('New Password', validators=[DataRequired(),Length(10,128), EqualTo('password2', message = 'Passwords must match')])
    password2 = PasswordField('Confirm New Password', validators = [DataRequired()])
    submit = SubmitField('Reset Password')

class ChangeEmailForm(Form):
    new_email = StringField('New Email', validators=[DataRequired(), Length(1, 128), Email(), EqualTo('new_email2', message='Emails must match')])
    new_email2 = StringField('Re-Enter Email', validators=[DataRequired(), Length(1, 128), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Change Email')