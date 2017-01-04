from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_principal import Permission, UserNeed

from app.security import app_permission_admin, create_user_permission
from . import dashboard
from .forms import ChangePasswordForm, ChangeEmailForm, UpdateUserProfileForm
from .. import db
from ..flask_sendgrid import send_email
from ..models import User


@dashboard.before_request
@login_required
def before_dashboard_request():
    pass


@dashboard.route('/user/<userid>/change_password', methods=['GET', 'POST'])
def change_password(userid):
    form = ChangePasswordForm()
    user = User.query.filter_by(id=userid).first_or_404()
    user_permission = create_user_permission(user.id)
    if not (user_permission.can() or app_permission_admin.can()):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        if user.verify_password(form.old_password.data):
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            flash('Your password has been changed.', 'success')
            return redirect(url_for('dashboard.user_profile', userid=user.id))
        else:
            flash('You entered an invalid password.', 'danger')
    return render_template("dashboard/change_password.html", form=form, user=user)


@dashboard.route('/user/<userid>/change_email', methods=['GET', 'POST'])
def change_email_request(userid):
    form = ChangeEmailForm()
    user = User.query.filter_by(id=userid).first_or_404()
    user_permission = create_user_permission(user.id)
    if not (user_permission.can() or app_permission_admin.can()):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        if user.verify_password(form.password.data):
            new_email = form.new_email.data
            user = User.query.filter_by(email=new_email).first()
            if user is not None:
                flash('Email is already registered.', 'warning')
            else:
                token = user.generate_email_change_token(new_email)
                send_email(subject='Unkani - Email Change', to=[new_email], template='auth/email/change_email',
                           token=token, user=user)
                flash('A confirmation email  has been sent to your new email.', 'info')
                return redirect(url_for('dashboard.user_profile', userid=user.id))
        else:
            flash('Invalid password.', 'danger')
    return render_template('dashboard/change_email.html', form=form, user=user)


@dashboard.route('/change_email/<token>')
def change_email(token):
    if current_user.change_email(token):
        flash('Your email has been updated.', 'success')
    else:
        flash('Invalid email change request.', 'danger')
    return redirect(url_for('dashboard.user_profile', userid=current_user.id))


@dashboard.route('/dashboard')
def dashboard_main():
    return render_template('dashboard/dashboard.html')


@dashboard.route('/user/<int:userid>', methods=['GET', 'POST'])
def user_profile(userid):
    form = UpdateUserProfileForm()
    user = User.query.filter_by(id=userid).first_or_404()
    user_permission = create_user_permission(user.id)
    if not (user_permission.can() or app_permission_admin.can()):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    # if not current_user.id == user.id:
    #     flash('You do not have access to this user profile.', 'danger')
    #     return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        username = None
        if form.username.data != user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash(
                    'The username {} is already taken. We kept your username the same.'.format(form.username.data),
                    'danger')
                username = user.username
            else:
                username = form.username.data
        else:
            username = form.username.data
        user.username = username
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.dob = form.dob.data
        user.description = form.about_me.data
        db.session.add(user)
        flash('Your profile has been updated.', 'success')

    form.username.data = user.username
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.dob.data = user.dob
    form.phone.data = user.phone
    form.about_me.data = user.description
    return render_template('dashboard/user_profile.html', form=form, user=user)


@dashboard.route('/admin/user_list', methods=['GET', 'POST'])
@app_permission_admin.require(http_exception=403)
def admin_user_list():
    userlist = User.query.order_by(User.id).all()
    return render_template('dashboard/admin_user_list.html', userlist=userlist)

