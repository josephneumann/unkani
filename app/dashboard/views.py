from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from app.auth.views import complete_logout
from app.flask_sendgrid import send_email
from app.security import *
from . import dashboard
from .forms import ChangePasswordForm, ChangeEmailForm, UpdateUserProfileForm
from .. import sa
from app.models import User, EmailAddress, Patient
from app.models.user import lookup_user_by_email, lookup_user_by_username
from app.api_v1.email_addresses import EmailAddressAPI
from app.api_v1.users import UserAPI


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
    if not user.is_accessible(requesting_user=current_user, other_permissions=[app_permission_userpasswordchange],
                              self_permissions=[app_permission_userpasswordchange]):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        if not form.password.data == form.password2.data:
            flash('Password entries did not match.', category='danger')
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
    if not user.is_accessible(requesting_user=current_user, other_permissions=[app_permission_userprofileupdate],
                              self_permissions=[app_permission_userprofileupdate]):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        if user.verify_password(form.password.data):
            new_email = form.new_email.data
            api = EmailAddressAPI(email=new_email, primary=True, active=True)
            api.run_validations()
            if api.errors['critical']:
                flash(
                    """A new email could not be created from the form data provided.  
                    You were re-directed to your own profile instead.""",
                    'danger')
                return redirect(url_for('dashboard.user_profile', userid=user.id))
            new_email, errors = api.make_object()
            if isinstance(new_email, EmailAddress):
                matching_email = lookup_user_by_email(email=new_email.email)
                if matching_email:
                    if matching_email.user == user:
                        token = user.generate_email_change_token(new_email=matching_email.email)
                        send_email(subject='Unkani - Email Change', to=[matching_email.email],
                                   template='auth/email/change_email',
                                   token=token, user=user)
                        flash(
                            'The email {} was previously registered to your user account.\
                              A confirmation email has been sent to that address to re-activate the email'.format(
                                matching_email.email), 'success')
                        return redirect(url_for('dashboard.user_profile', userid=user.id))
                    else:
                        flash(
                            'The email {} is already registered to another user.'.format(new_email.email), 'danger')
                        return redirect(url_for('dashboard.user_profile', userid=user.id))
                else:
                    user.email_addresses.append(new_email)
                    token = user.generate_email_change_token(new_email=new_email.email)
                    send_email(subject='Unkani - Email Change', to=[new_email.email],
                               template='auth/email/change_email',
                               token=token, user=user)
                    flash(
                        """The email {} has been associated with your account.  A confirmation email has been sent to that address to activate the email""".format(
                            new_email.email), 'success')
                    return redirect(url_for('dashboard.user_profile', userid=user.id))
            else:
                raise ValueError("A new email_address record could not be generated from the form data.")
        else:
            flash('Could not verify the password provided.', category='danger')
    return render_template('dashboard/change_email.html', form=form, user=user)


@dashboard.route('/change_email/<token>')
def change_email(token):
    try:
        current_user.process_change_email_token(token)
        flash('Your email has been updated.', 'success')
    except:
        flash('Invalid email change request.', 'danger')
    return redirect(url_for('dashboard.user_profile', userid=current_user.id))


@dashboard.route('/dashboard')
def dashboard_main():
    return render_template('dashboard/dashboard.html')


@dashboard.route('/user/<int:userid>', methods=['GET', 'POST'])
def user_profile(userid):
    form = UpdateUserProfileForm()
    user = User.query.filter_by(id=userid).first_or_404()
    if not user.is_accessible(requesting_user=current_user, other_permissions=[app_permission_userprofileupdate],
                              self_permissions=[app_permission_userprofileupdate]):
        flash('You do not have access to this user profile.  You were re-directed to your own profile instead.',
              'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if form.validate_on_submit():
        api = UserAPI()
        api.user = user
        api.username = form.username.data
        api.first_name = form.first_name.data
        api.last_name = form.last_name.data
        api.dob = form.dob.data
        api.description = form.about_me.data
        api.phone_number = form.phone.data

        api.run_validations()

        if not api.errors['critical'].get('username'):
            if api.username and api.username != api.user.username:
                username_match = lookup_user_by_username(api.username)
                if username_match and username_match != api.user:
                    api.errors['critical']['username'] = 'The username {} is already registered.'.format(api.username)
                    api.username = None

        if api.errors['critical']:
            for key in api.errors['critical']:
                if isinstance(api.errors['critical'][key], dict):
                    for nested_key in api.errors['critical'][key]:
                        flash(api.errors['critical'][key][nested_key], 'danger')
                flash(api.errors['critical'][key], 'danger')
            flash('User could not be updated due to critical errors.', 'danger')

        if api.errors['warning']:
            for key in api.errors['warning']:
                if isinstance(api.errors['warning'][key], dict):
                    for nested_key in api.errors['warning'][key]:
                        flash(api.errors['warning'][key][nested_key], 'warning')
                else:
                    flash(api.errors['warning'][key], 'warning')

        if not api.errors['critical']:
            updated_user, errors = api.make_object()
            if updated_user:
                sa.session.add(updated_user)
                flash('User profile has been updated.', 'success')

    form.username.data = user.username.lower()
    form.first_name.data = user.first_name.title()
    form.last_name.data = user.last_name.title()
    form.dob.data = getattr(user, 'dob', None)
    if user.phone_number:
        form.phone.data = user.phone_number.formatted_phone
    form.about_me.data = getattr(user, 'description', None)
    return render_template('dashboard/user_profile.html', form=form, user=user)


@dashboard.route('/user/<int:userid>/deactivate', methods=['GET'])
def deactivate_user(userid):
    user = User.query.get_or_404(userid)
    if not user.is_accessible(requesting_user=current_user, other_permissions=[app_permission_useractivation],
                              self_permissions=[app_permission_useractivation]):
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
        flash("The account with email {} was successfully deactivated".format(user.email.email), "info")
        return redirect(url_for('dashboard.dashboard_main'))


@dashboard.route('/admin/user_list', methods=['GET', 'POST'])
def admin_user_list():
    if not (app_permission_useradmin.can() or role_permission_superadmin.can()):
        abort(403)
    userlist = User.query.order_by(User.id).all()
    for user in userlist:
        if not user.is_accessible(requesting_user=current_user):
            userlist.pop(userlist.index(user))
    return render_template('dashboard/admin_user_list.html', userlist=userlist)


@dashboard.route('/admin/patient_list', methods=['GET', 'POST'])
def admin_patient_list():
    if not (app_permission_patientadmin.can() or role_permission_superadmin.can()):
        abort(403)
    patient_list = Patient.query.order_by(Patient.id).all()
    return render_template('dashboard/patient_list.html', patient_list=patient_list)


@dashboard.route('/admin/user/<int:userid>/confirm', methods=['GET'])
def force_confirm_user(userid):
    user = User.query.get_or_404(userid)
    if not user.is_accessible(requesting_user=current_user,
                              other_permissions=[app_permission_userforceconfirmation],
                              self_permissions=[app_permission_userforceconfirmation]):
        flash("You do not have permission to confirm user with id {}".format(user.id), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if user.confirmed:
        flash("The user {} is already confirmed.".format(user.email.email), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    user.confirmed = True
    sa.session.add(user)
    sa.session.commit()
    flash("User account {} has been confirmed manually.".format(user.email.email), 'success')
    return redirect(url_for('dashboard.user_profile', userid=userid))


@dashboard.route('/admin/user/<int:userid>/unconfirm', methods=['GET'])
def revoke_user_confirmation(userid):
    user = User.query.get_or_404(userid)
    if not user.is_accessible(requesting_user=current_user,
                              other_permissions=[app_permission_userforceconfirmation],
                              self_permissions=[app_permission_userforceconfirmation]):
        flash("You do not have permission to un-confirm user with id {}".format(user.id), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    if not user.confirmed:
        flash("The user {} is already un-confirmed.".format(user.email.email), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    user.confirmed = False
    sa.session.add(user)
    sa.session.commit()
    flash("User account {} has had their confirmed status revoked manually.".format(user.email.email), 'success')
    return redirect(url_for('dashboard.user_profile', userid=userid))


@dashboard.route('/admin/user/<int:userid>/reset_password', methods=['GET'])
def reset_user_password(userid):
    user = User.query.get_or_404(userid)
    if not user.is_accessible(requesting_user=current_user,
                              other_permissions=[app_permission_userpasswordreset],
                              self_permissions=[app_permission_userpasswordreset]):
        flash("You do not have permission to confirm user with id {}".format(user.id), 'danger')
        return redirect(url_for('dashboard.user_profile', userid=current_user.id))
    token = user.generate_reset_token()
    send_email(to=[user.email.email], subject='Reset Your Password', template='auth/email/reset_password'
               , user=user, token=token, next=request.args.get('next'))
    flash('An email with instructions for resetting the user password has been sent to {}.'.format(user.email.email),
          'info')
    return redirect(url_for('dashboard.user_profile', userid=userid))
