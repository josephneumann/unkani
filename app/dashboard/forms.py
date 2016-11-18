from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Password', render_kw={"required": "true", "placeholder": "Current Password"})
    password = PasswordField('New Password', render_kw={"placeholder": "New Password", "required": "true",
                                                        "id": "changepasswordnewpassword1", "minLength": "10",
                                                        "maxLength": "128"})
    password2 = PasswordField('Confirm New Password', render_kw={"placeholder": "Confirm New Password",
                                                                 "equalTo": "#changepasswordnewpassword1",
                                                                 "required": "true", "minLength": "10",
                                                                 "maxLength": "128"})
    submit = SubmitField('Change Password')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email',
                            render_kw={"id": "changeemailformemail1", "placeholder": "Email", "required": "true",
                                       "maxLength": "128", "email": "true"})
    new_email2 = StringField('Re-Enter Email',
                             render_kw={"equalTo": "#changeemailformemail1", "placeholder": "Confirm Email",
                                        "required": "true", "maxLength": "128", "email": "true"})
    password = PasswordField('Password', render_kw={"placeholder": "Password", "required": "true"})
    submit = SubmitField('Change Email')


class UpdateUserProfileForm(FlaskForm):
    first_name = StringField('First Name',
                             render_kw={"placeholder": "First Name", "required": "true", "maxLength": "128"})
    last_name = StringField('Last Name', render_kw={"placeholder": "Last Name", "required": "true", "maxLength": "128"})
    dob = DateField('DOB', render_kw={"required": "true", "placeholder": "Date of Birth"})
    phone = StringField('phone', render_kw={"placeholder": "Phone", "required": "true"})
    username = StringField('Username', render_kw={"placeholder": "Username", "required": "true", "minLength": "5",
                                                  "maxLength": "128"})
    submit = SubmitField('Register')
