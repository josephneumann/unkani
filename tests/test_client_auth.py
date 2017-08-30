from flask import url_for, g, session
from flask_login import current_user
from app import sa
from app.models import User
from app.security import *
from tests.test_client_utils import BaseClientTestCase, user_dict


class AuthViewsFormsTestCase(BaseClientTestCase):
    def test_login_page_render(self):
        response = self.client.get(url_for('auth.login'))
        self.assert200(response)
        self.assert_template_used('auth/login.html')

    def test_login_identity_sets(self):
        self.create_test_user()
        with self.client:
            response = self.login()
            identity = g.get('identity', None)
            self.assertTemplateUsed('dashboard/dashboard.html')
            self.assert200(response)
            self.assertFalse(current_user.is_anonymous, msg="Current user was anonymous after login.")
            user = self.get_test_user()
            self.assertEqual(current_user.id, user.id,
                             msg="The current_user object was not the same as the test user login.")
            self.assertEqual(identity.user.id, current_user.id, msg="The identity.user was not equal to current user.")
            self.assertTrue(identity.can(role_permission_user),
                            msg="After login, the user did not have the user role permission")
            needs_provided = getattr(identity, 'provides', None)
            self.assertIsNotNone(needs_provided, msg='Flask-Principal identity did not provide any Needs.')
            role_need_count = 0
            apppermission_need_count = 0
            for need in needs_provided:
                self.assertIsInstance(obj=need, cls=Need,
                                      msg='Flask-Principal identity.provides included objects that were not of the class Need.')

    def test_logout_request(self):
        with self.client:
            self.create_test_user()
            self.login()
            response = self.client.get(url_for('auth.logout'), follow_redirects=False)
            self.assertStatus(response, 302)
            identity = g.get('identity', None)
            identity_name = session.get('identity.name', None)
            self.assertTrue(current_user.is_anonymous, msg="Current user was not set to anonymous on logout.")
            self.assertIsNone(identity_name)
            self.assertTrue(identity.user.is_anonymous)
            self.assertMessageFlashed(message='Successfully logged out.', category='success')

    def test_login_invalid_login(self):
        self.create_test_user()
        with self.client:
            # Try wrong password
            response = self.login(password="foobar")
            self.assert200(response)
            self.assertTemplateUsed('auth/login.html')
            self.assertTrue(current_user.is_anonymous, msg="Invalid login pw did not result in an anonymous user.")

            # Try invalid email
            response = self.login(email='foo.bar@example.com')
            self.assert200(response)
            self.assertTemplateUsed('auth/login.html')
            self.assertTrue(current_user.is_anonymous, msg="Invalid login email did not result in anonymous user.")

    def test_register_page_render(self):
        response = self.client.get(url_for('auth.register'))
        self.assert200(response)
        self.assert_template_used('auth/register.html')

    def test_register_creates_unconfirmed_user(self):
        with self.client:
            # Register new user
            response = self.client.post(url_for('auth.register'), data={
                'email': user_dict.get("email"),
                'username': user_dict.get("username"),
                'password': user_dict.get("password"),
                'first_name': user_dict.get("first_name"),
                'last_name': user_dict.get("last_name")
            }, follow_redirects=True)
            self.assert200(response)

            # Check new user was created after registration and was marked as unconfirmed
            user = self.get_test_user()
            self.assertIsNotNone(user, msg="User was not created with registration post.")
            self.assertFalse(user.confirmed, msg="User was created with registration but was automatically confirmed.")

            # Login with the new account and check that redirect to unconfirmed page happens
            self.login()
            self.assert200(response)
            self.assert_template_used('auth/unconfirmed.html')
            self.assertEqual(current_user.id, user.id)

    def test_register_existing_user(self):
        self.create_test_user()

        # Try registering same email
        response = self.client.post(url_for('auth.register'), data={
            'email': user_dict.get("email"),
            'username': user_dict.get("foo.bar"),
            'password': user_dict.get("password"),
            'first_name': user_dict.get("first_name"),
            'last_name': user_dict.get("last_name")
        }, follow_redirects=True)
        self.assertTrue(
            b'already registered to another user' in response.data
        )

        # Try registering same username
        response = self.client.post(url_for('auth.register'), data={
            'email': user_dict.get("foo.bar@example.com"),
            'username': user_dict.get("foo.bar"),
            'password': user_dict.get("password"),
            'first_name': user_dict.get("first_name"),
            'last_name': user_dict.get("last_name")
        }, follow_redirects=True)

        self.assertTrue(
            b'already registered to another user' in response.data
        )

    def test_account_confirmation(self):
        # Create two users for testing
        self.create_test_user(confirmed=False)
        self.create_test_user(username="jane.doe", email="jane.doe@example.com", confirmed=False)
        user1 = User.query.filter_by(_username='JOHN.DOE').first()
        user2 = User.query.filter_by(_username='JANE.DOE').first()
        token1 = user1.generate_confirmation_token()
        token2 = user2.generate_confirmation_token()

        # Login user1 to test account confirmation
        self.login()

        # Test invalid token supply generates flashed message
        response = self.client.get(url_for('auth.confirm', token=token2),
                                   follow_redirects=True)
        self.assertFalse(user1.confirmed)

        # Test valid confirmation token confirms user
        response = self.client.get(url_for('auth.confirm', token=token1),
                                   follow_redirects=True)
        self.assertTrue(user1.confirmed)

        # Test unconfirmed page redirects to index
        response = self.client.get(url_for('auth.unconfirmed'), follow_redirects=False)
        self.assertRedirects(response, location=url_for('main.landing'))

        # Test that further client.py to confirmation page are redirected to index
        response = self.client.get(url_for('auth.confirm', token=token1),
                                   follow_redirects=False)
        self.assertRedirects(response=response, location=url_for('main.landing'))

    def test_account_confirmation_email_resend(self):
        self.create_test_user(confirmed=False)
        user = self.get_test_user()
        token = user.generate_confirmation_token()
        with self.client:
            self.login()

            # Test resend confirmation route
            response = self.client.get(url_for('auth.resend_confirmation', userid=user.id), follow_redirects=True)
            self.assert200(response)
            self.assertTrue(
                b'A new confirmation email has been sent' in response.data)

            # Text that resend confirmation route redirects if user is already confirmed
            user.confirmed = True
            sa.session.add(user)
            sa.session.commit()

            response = self.client.get(url_for('auth.resend_confirmation', userid=user.id), follow_redirects=False)
            self.assertRedirects(response=response, location=url_for('main.landing'))

    def test_account_confirmation_email_resend_access(self):
        with self.client:
            self.create_test_user()
            self.create_test_user(email='JANE.DOE@EXAMPLE.COM', username='JANE.DOE', confirmed=False)

            u1 = self.get_test_user()
            u2 = self.get_test_user(username='JANE.DOE')

            # Login user1
            self.login()

            # Request confirmation resend for user2 as user role
            response = self.client.get(url_for('auth.resend_confirmation', userid=u2.id), follow_redirects=False)
            self.assertStatus(response=response, status_code=302)
            self.assertMessageFlashed(message='You do not have permission to resend the confirmation for this user.',
                                      category='danger')

    def test_reset_password_not_available_to_logged_in_user(self):
        self.create_test_user()
        with self.client:
            self.login()
            response = self.client.get(url_for('auth.reset_password_request'), follow_redirects=False)
            self.assertRedirects(response, url_for('main.landing'))

    def test_reset_password_request_successful(self):
        # Reset password template gets rendered on get
        self.create_test_user()

        # Reset password email gets sent
        response = self.client.post(url_for('auth.reset_password_request'), data={
            'email': user_dict.get('email')}, follow_redirects=True)
        self.assert200(response)
        self.assertMessageFlashed('An email with instructions for resetting your password has been sent to you.',
                                  'info')

    def test_reset_password_for_inactive_user(self):
        with self.client:
            self.create_test_user()
            user = self.get_test_user()
            user.active = False
            sa.session.add(user)
            sa.session.commit()
            response = self.client.post(url_for('auth.reset_password_request'), data={
                'email': user_dict.get('email')}, follow_redirects=True)
            self.assertMessageFlashed('That user account is no longer active.', 'danger')
            self.assertTemplateUsed('auth/reset_password_request.html')

    def test_reset_password_for_user_does_not_exist(self):
        self.create_test_user()
        response = self.client.post(url_for('auth.reset_password_request'), data={
            'email': 'john.doe2@example.com'}, follow_redirects=True)
        self.assertMessageFlashed('A user account with that email does not exist.', 'danger')
        self.assertTemplateUsed('auth/reset_password_request.html')

    def test_logged_in_user_cannot_request_password_reset_by_email(self):
        self.create_test_user()
        self.login()
        response = self.client.get(url_for('auth.reset_password', token='sampletoken'),
                                   follow_redirects=True)
        self.assertTemplateUsed('public/index.html')

    def test_successful_password_reset_form_render(self):
        self.create_test_user()
        user = self.get_test_user()
        token = user.generate_reset_token()
        response = self.client.get(url_for('auth.reset_password_request', token=token),
                                   follow_redirects=True)
        self.assertTemplateUsed('auth/reset_password_request.html')

    def test_password_reset_for_invalid_email(self):
        self.create_test_user()
        user = self.get_test_user()
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.reset_password', token=token), data={
            'email': 'foo.bar@example.com', 'password': 'testpw2'}, follow_redirects=True)
        self.assertMessageFlashed('That does not appear to be an active primary email for an unkani account.', 'danger')

    def test_valid_password_reset_post(self):
        self.create_test_user()
        with self.client:
            user = self.get_test_user()
            token = user.generate_reset_token()
            response = self.client.post(url_for('auth.reset_password', token=token), data={
                'email': user_dict.get('email'), 'password': 'testpw2', 'password2': 'testpw2'}, follow_redirects=True)
            self.assert200(response)
            self.assertMessageFlashed('Your password has been reset.', 'success')
            self.assertTrue(user.verify_password(password='testpw2'))

    def test_invalid_userid_in_password_reset_token(self):
        self.create_test_user()
        self.create_test_user(username='JANE.DOE', email='JANE.DOE@EXAMPLE.COM')
        user = User.query.filter_by(_username='JANE.DOE').first()
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.reset_password', token=token), data={
            'email': user_dict.get('email'), 'password': 'testpw2',
            'password2': 'testpw2'}, follow_redirects=True)

        # Test that password was not changed
        self.assertMessageFlashed('There was an error resetting your password.', 'danger')
        self.assertFalse(user.verify_password(password='testpw2'))
        self.assertTrue(user.verify_password(password='testpw'))

    def test_render_password_reset_template(self):
        self.create_test_user()
        user = self.get_test_user()
        token = user.generate_reset_token()
        response = self.client.get(url_for('auth.reset_password', token=token), follow_redirects=True)
        self.assertTemplateUsed('auth/reset_password.html')

    def test_last_seen_ping_on_login(self):
        self.create_test_user()
        self.login()
        user = self.get_test_user()
        last_seen = user.last_seen
        self.assertTrue(last_seen)

    def test_login_with_inactive_user(self):
        self.create_test_user()
        user = self.get_test_user()
        user.active = False
        sa.session.add(user)
        sa.session.commit()

        with self.client:
            response = self.login()
            self.assert200(response)
            self.assertTemplateUsed('auth/login.html')
            self.assertTrue(current_user.is_anonymous, msg="Invalid login pw did not result in an anonymous user.")
