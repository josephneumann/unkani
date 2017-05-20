from flask import render_template, redirect, request, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import identity_changed, Identity, AnonymousIdentity, identity_loaded, UserNeed, RoleNeed

from app.flask_sendgrid import send_email
from app.security import AppPermissionNeed, create_user_permission, app_permission_usercreate, \
    return_template_context_permissions
from . import auth
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from .. import sa
from ..models import User, Role


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static' \
                and request.endpoint[:5] != 'main.':
            return redirect(url_for('auth.unconfirmed'))


@auth.context_processor
def auth_context_processor():
    app_permission_dict = return_template_context_permissions()
    return app_permission_dict


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('A user account with the email address {} was not found.'.format(form.email.data), 'danger')
        elif user.verify_password(form.password.data):
            if user.active:
                login_user(user, form.remember_me.data)
                identity_changed.send(current_app._get_current_object(),
                                      identity=Identity(user.id))
                return redirect(request.args.get('next') or url_for('dashboard.dashboard_main'))
            else:
                flash('The user account with the email address {} been deactivated.'.format(form.email.data), 'danger')
        else:
            flash('Invalid password provided for user {}.'.format(user.email), 'danger')
    return render_template('auth/login.html', form=form)


def complete_logout():
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())


@auth.route('/logout')
@login_required
def logout():
    complete_logout()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('main.landing'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('The email {} is already registered. Please enter a different email address.'.format(form.email.data),
                  'danger')

        if User.query.filter_by(username=form.username.data).first():
            flash(
                'The username {} is already registered.  Please enter a different username.'.format(form.username.data),
                'danger')

        else:
            user = User(email=form.email.data, first_name=form.first_name.data, last_name=form.last_name.data,
                        username=form.username.data, password=form.password.data)
            sa.session.add(user)
            sa.session.commit()
            token = user.generate_confirmation_token()
            send_email(to=[user.email], user=user, token=token,
                       subject='Confirm Your Account', template='auth/email/confirm')
            flash('A confirmation message has been sent to {}.'.format(user.email), 'info')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('Your account has already been confirmed.', 'success')
        return redirect(url_for('main.landing'))
    if current_user.confirm(token):
        flash('You have confirmed your account {}.'.format(current_user.email), 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('main.landing'))


@auth.route('/resend_confirmation/<int:userid>')
@login_required
def resend_confirmation(userid):
    user = User.query.get_or_404(userid)
    user_permission = create_user_permission(user.id)
    if not (user_permission.can() or app_permission_usercreate.can()):
        flash('You do not have permission to resend the confirmation for this user.', 'danger')
        if request.referrer != url_for('auth.unconfirmed'):
            return redirect(request.referrer)
        else:
            return redirect(url_for('main.landing'))
    if user.confirmed:
        flash("The user {} is already confirmed".format(user.email), "danger")
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('main.landing'))
    else:
        token = user.generate_confirmation_token()
        send_email(to=[user.email], subject='Confirm Your Account', template='auth/email/confirm'
                   , user=user, token=token)
        flash('A new confirmation email has been sent to the email address "{}".'.format(current_user.email), 'info')
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
    # Update the identity with the roles that the user provides
    if hasattr(current_user, 'role_id'):
        role = Role.query.filter_by(id=current_user.role_id).first()
        identity.provides.add(RoleNeed(role.name))
        app_permissions = role.app_permissions
        for app_permission_name in app_permissions:
            identity.provides.add(AppPermissionNeed(str(app_permission_name)))
