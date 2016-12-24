from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from . import dashboard
from .forms import ChangePasswordForm, ChangeEmailForm, UpdateUserProfileForm
from .. import db
from ..models import User
from ..flask_sendgrid import send_email
from flask_principal import Permission, RoleNeed

admin_permission = Permission(RoleNeed('Admin'))
user_permission = Permission(RoleNeed('User'))


@dashboard.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been changed.', 'success')
            return redirect(url_for('dashboard.user_profile', userid=current_user.id))
        else:
            flash('You entered an invalid password.', 'danger')
    return render_template("dashboard/change_password.html", form=form)


@dashboard.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.new_email.data
            user = User.query.filter_by(email=new_email).first()
            if user is not None:
                flash('Email is already registered.', 'warning')
            else:
                token = current_user.generate_email_change_token(new_email)
                send_email(subject='Unkani - Email Change', to=[new_email], template='auth/email/change_email',
                           token=token, user=current_user)
                flash('A confirmation email  has been sent to your new email.', 'info')
                return redirect(url_for('dashboard.user_profile', userid=current_user.id))
        else:
            flash('Invalid password.', 'danger')
    return render_template('dashboard/change_email.html', form=form)


@dashboard.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email has been updated.', 'success')
    else:
        flash('Invalid email change request.', 'danger')
    return redirect(url_for('dashboard.user_profile', userid=current_user.id))


@dashboard.route('/dashboard')
@login_required
def dashboard_main():
    return render_template('dashboard/dashboard.html')


@dashboard.route('/user/<userid>', methods=['GET', 'POST'])
@login_required
def user_profile(userid):
    form = UpdateUserProfileForm()
    user = User.query.filter_by(id=userid).first()
    if not user or current_user.id != user.id:
        flash('You do not have access to this user profile.', 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        username = None
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                username = current_user.username
                flash(
                    'The username '
                    + form.username.data
                    + ''' is already taken. We kept your username the same.'''
                    , 'danger')
        else:
            username = form.username.data
        user.username = username
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.dob = form.dob.data
        db.session.add(user)
        flash('Your profile has been updated.', 'success')

    form.username.data = current_user.username
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.dob.data = current_user.dob
    form.phone.data = current_user.phone
    return render_template('dashboard/user_profile.html', form=form)


@dashboard.route('/admin/user_list', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def admin_user_list():
    userlist = User.query.order_by(User.id).all()
    return render_template('dashboard/admin_user_list.html', userlist=userlist)
