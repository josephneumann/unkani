from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField


class LoginForm(FlaskForm):
    email = StringField('Email',
                        render_kw={"placeholder": "Email", "required": "true", "email": "true", "maxLength": "128"})
    password = PasswordField('Password', render_kw={"placeholder": "Password", "required": "true"})
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name',
                             render_kw={"placeholder": "First Name", "required": "true", "maxLength": "128"})
    last_name = StringField('Last Name', render_kw={"placeholder": "Last Name", "required": "true", "maxLength": "128"})
    # dob=DateField('DOB', validators=[DataRequired])
    email = StringField('Email',
                        render_kw={"placeholder": "Email", "required": "true", "email": "true", "maxLength": "128"})
    # phone=StringField('phone', validators=None)
    username = StringField('Username', render_kw={"placeholder": "Username", "required": "true", "minLength": "5",
                                                  "maxLength": "128"})
    password = PasswordField('Password', render_kw={"placeholder": "Password", "required": "true"})
    submit = SubmitField('Register')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email',
                        render_kw={"placeholder": "Email", "required": "true", "email": "true", "maxLength": "128"})
    submit = SubmitField('Reset Password')


class ResetPasswordForm(FlaskForm):
    email = StringField('Email',
                        render_kw={"placeholder": "Email", "required": "true", "email": "true", "maxLength": "128"})
    password = PasswordField('New Password',
                             render_kw={"id": "resetpasswordform1", "placeholder": "Password", "required": "true"})
    password2 = PasswordField('Confirm New Password',
                              render_kw={"equalTo": "#resetpasswordform1", "placeholder": "Confirm Password",
                                         "required": "true"})
    submit = SubmitField('Reset Password')


