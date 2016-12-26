from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user, current_app
from flask_principal import identity_changed, Identity, AnonymousIdentity, Permission, RoleNeed, UserNeed, \
    identity_loaded

from . import auth
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from .. import db
from ..models import User, Role
from ..flask_sendgrid import send_email

# flash('Info message, blue', 'info')
# flash('Success message, green.', 'success')
# flash('Warning message, yellow.', 'warning')
# flash('Danger message, red/orange.', 'danger')


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static' \
                and request.endpoint[:5] != 'main.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
            return redirect(request.args.get('next') or url_for('dashboard.dashboard_main'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    # Remove and reset the user sesssion
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    flash('Successfully logged out.', 'success')
    return redirect(url_for('main.landing'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email is already registered. Please enter a different email address '
                  'or recover your password for your existing account to proceed.', 'danger')

        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.  Please enter a different username or '
                  'recover your password for your existing account to proceed.', 'danger')

        else:
            user = User(email=form.email.data, first_name=form.first_name.data, last_name=form.last_name.data,
                        username=form.username.data, password=form.password.data)
            user.avatar_hash = user.gravatar()
            db.session.add(user)
            db.session.commit()
            token = user.generate_confirmation_token()
            send_email(to=[user.email], user=user, token=token,
                       subject='Confirm Your Account', template='auth/email/confirm')
            flash('A confirmation message has been sent to your email.', 'info')
            return (redirect(url_for('auth.login')))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('Your account has already been confirmed.', 'success')
        return redirect(url_for('main.landing'))
    if current_user.confirm(token):
        flash('You have confirmed your account.', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('main.landing'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(to=[current_user.email], subject='Confirm Your Account', template='auth/email/confirm'
               , user=current_user, token=token)
    flash('A new confirmation email has been sent to your email address.', 'info')
    return redirect(url_for('main.landing'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.landing'))
    return render_template('auth/unconfirmed.html')


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.landing'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.active:
                token = user.generate_reset_token()
                send_email(to=[user.email], subject='Reset Your Password', template='auth/email/reset_password'
                           , user=user, token=token, next=request.args.get('next'))

                flash('An email with instructions for resetting your password has been sent to you.', 'info')
                return redirect(url_for('auth.login'))
            else:
                flash('That user account is no longer active.', 'danger')
                return render_template('auth/reset_password_request.html', form=form)
        else:
            flash('A user account with that password does not exist. '
                  'Please enter a valid email address.', 'danger')
            return render_template('auth/reset_password_request.html', form=form)

    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.landing'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('That does not appear to be a valid email.', 'danger')
            return redirect(url_for('main.landing'))
        new_password = form.password.data
        if user.reset_password(token, new_password):
            flash('Your password has been reset.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('There was an error resetting your password.', 'danger')
            return redirect(url_for('main.landing'))
    return render_template('auth/reset_password.html', form=form)


@identity_loaded.connect
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'role_id'):
        role = Role.query.filter_by(id=current_user.role_id).first()
        role_name = role.name
        identity.provides.add(RoleNeed(role_name))
