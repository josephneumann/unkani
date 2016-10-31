from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from .. models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Length(1,128),Email()],render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired(message='Password is required')],render_kw={"placeholder": "Password"})
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1,128)],render_kw={"placeholder": "First Name"})
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1,128)],render_kw={"placeholder": "Last Name"})
    #dob=DateField('DOB', validators=[DataRequired])
    email = StringField('Email', validators=[DataRequired(),Length(1,128),Email()],render_kw={"placeholder": "Email"})
    #phone=StringField('phone', validators=None)
    username = StringField('Username', validators=[DataRequired(), Length(5,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', flags = 0, message = 'Usernames must have only letters, numbers, dots or underscores')],render_kw={"placeholder": "Username"})
    password = PasswordField('Password', validators=[DataRequired(),Length(10,128), EqualTo('password2', message = 'Passwords must match')],render_kw={"placeholder": "Password"})
    password2 = PasswordField('Confirm Password', validators = [DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Password', validators=[DataRequired()],render_kw={"placeholder": "Current Password"})
    password = PasswordField('New Password', validators=[DataRequired(),Length(10,128), EqualTo('password2', message = 'Passwords must match')],render_kw={"placeholder": "New Password"})
    password2 = PasswordField('Confirm New Password', validators = [DataRequired()],render_kw={"placeholder": "Confirm New Password"})
    submit = SubmitField('Change Password')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 128), Email()],render_kw={"placeholder": "Email"})
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 128), Email()],render_kw={"placeholder": "Email"})
    password = PasswordField('New Password', validators=[DataRequired(),Length(10,128), EqualTo('password2', message = 'Passwords must match')],render_kw={"placeholder": "Password"})
    password2 = PasswordField('Confirm New Password', validators = [DataRequired()],render_kw={"placeholder": "Password"})
    submit = SubmitField('Reset Password')

class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email', validators=[DataRequired(), Length(1, 128), Email(), EqualTo('new_email2', message='Emails must match')],render_kw={"placeholder": "New Email"})
    new_email2 = StringField('Re-Enter Email', validators=[DataRequired(), Length(1, 128), Email()],render_kw={"placeholder": "Confirm New Email"})
    password = PasswordField('Password', validators=[DataRequired()],render_kw={"placeholder": "Password"})
    submit = SubmitField('Change Email')