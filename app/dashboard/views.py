from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app.auth.views import complete_logout
from app.security import *
from . import dashboard
from .forms import ChangePasswordForm, ChangeEmailForm, UpdateUserProfileForm
from .. import sa
from ..flask_sendgrid import send_email
from ..models import User


@dashboard.before_request
@login_required
def before_dashboard_request():
    pass


@dashboard.context_processor
def dashboard_context_processor():
    app_permission_dict = return_template_context_permissions()
    return app_permission_dict


@dashboard.route('/user/<userid>/change_password', methods=['GET', 'POST'])
def change_password(userid):
    form = ChangePasswordForm()
    user = User.query.filter_by(id=userid).first_or_404()
    if not current_user.has_access_to_user_operation(user=user, other_permissions=[app_permission_userpasswordchange]):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        if user.verify_password(form.old_password.data):
            user.password = form.password.data
            sa.session.add(user)
            sa.session.commit()
            flash('Your password has been changed.', 'success')
            return redirect(url_for('dashboard.user_profile', userid=user.id))
        else:
            flash('You entered an invalid password.', 'danger')
    return render_template("dashboard/change_password.html", form=form, user=user)


@dashboard.route('/user/<userid>/change_email', methods=['GET', 'POST'])
def change_email_request(userid):
    form = ChangeEmailForm()
    user = User.query.filter_by(id=userid).first_or_404()
    if not current_user.has_access_to_user_operation(user=user, other_permissions=[app_permission_userprofileupdate]):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        if user.verify_password(form.password.data):
            new_email = form.new_email.data
            user2 = User.query.filter_by(email=new_email).first()
            if user2 is not None:
                flash('Email is already registered.', 'warning')
            else:
                token = user.generate_email_change_token(new_email=new_email)
                send_email(subject='Unkani - Email Change', to=[new_email], template='auth/email/change_email',
                           token=token, user=user)
                flash('A confirmation email has been sent to your new email.', 'info')
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
    if not current_user.has_access_to_user_operation(user=user, other_permissions=[app_permission_userprofileupdate]):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
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
        sa.session.add(user)
        flash('Your profile has been updated.', 'success')

    form.username.data = user.username
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.dob.data = user.dob
    form.phone.data = user.phone
    form.about_me.data = user.description
    return render_template('dashboard/user_profile.html', form=form, user=user)


@dashboard.route('/user/<int:userid>/deactivate', methods=['GET'])
def deactivate_user(userid):
    user = User.query.get_or_404(userid)
    if not current_user.has_access_to_user_operation(user=user, other_permissions=[app_permission_userdeactivate]):
        flash("You do not have permission to deactivate user with id {}".format(userid))
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if user.id == current_user.id:
        complete_logout()
        user.active = False
        sa.session.add(user)
        sa.session.commit()
        flash("Your account has been deactivated and you have been logged out.", "info")
        return redirect(url_for('main.landing'))
    else:
        user.active = False
        sa.session.add(user)
        sa.session.commit()
        flash("The account with email {} was successfully deactivated".format(user.email), "info")
        return redirect(url_for('dashboard.dashboard_main'))


@dashboard.route('/admin/user_list', methods=['GET', 'POST'])
def admin_user_list():
    if not (role_permission_admin.can() or role_permission_superadmin.can()):
        abort(403)
    userlist = User.query.order_by(User.id).all()
    for user in userlist:
        if not current_user.has_access_to_user_operation(user=user):
            userlist.pop(userlist.index(user))
    return render_template('dashboard/admin_user_list.html', userlist=userlist)


@dashboard.route('/admin/user/<int:userid>/confirm', methods=['GET'])
def force_confirm_user(userid):
    user = User.query.get_or_404(userid)
    if not current_user.has_access_to_user_operation(user=user,
                                                     other_permissions=[app_permission_userforceconfirmation]):
        flash("You do not have permission to confirm user with id {}".format(user.id), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if user.confirmed:
        flash("The user {} is already confirmed.".format(user.email), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    user.confirmed = True
    sa.session.add(user)
    sa.session.commit()
    flash("User account {} has been confirmed manually.".format(user.email), 'success')
    return redirect(url_for('dashboard.user_profile', userid=userid))


@dashboard.route('/admin/user/<int:userid>/unconfirm', methods=['GET'])
def revoke_user_confirmation(userid):
    user = User.query.get_or_404(userid)
    if not current_user.has_access_to_user_operation(user=user,
                                                     other_permissions=[app_permission_userforceconfirmation]):
        flash("You do not have permission to un-confirm user with id {}".format(user.id), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if not user.confirmed:
        flash("The user {} is already un-confirmed.".format(user.email), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    user.confirmed = False
    sa.session.add(user)
    sa.session.commit()
    flash("User account {} has had their confirmed status revoked manually.".format(user.email), 'success')
    return redirect(url_for('dashboard.user_profile', userid=userid))


@dashboard.route('/admin/user/<int:userid>/reset_password', methods=['GET'])
def reset_user_password(userid):
    user = User.query.get_or_404(userid)
    if not current_user.has_access_to_user_operation(user=user,
                                                     other_permissions=[app_permission_userpasswordreset]):
        flash("You do not have permission to confirm user with id {}".format(user.id), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    token = user.generate_reset_token()
    send_email(to=[user.email], subject='Reset Your Password', template='auth/email/reset_password'
               , user=user, token=token, next=request.args.get('next'))
    flash('An email with instructions for resetting the user password has been sent to {}.'.format(user.email), 'info')
    return redirect(url_for('dashboard.user_profile', userid=userid))
