from flask import url_for
from flask_testing import TestCase
from app import db, create_app as create_application
from app.models import User, Role


class AuthViewsFormsTestCase(TestCase):
    render_templates = True

    def create_app(self):
        app = create_application('testing')
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()
        Role.initialize_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.create_all()

    def test_login_page_render(self):
        response = self.client.get(url_for('auth.login'))
        self.assert_template_used('auth/login.html')

    def test_register_page_render(self):
        response = self.client.get(url_for('auth.register'))
        self.assert_template_used('auth/register.html')

    def test_invalid_login_message(self):
        u = User(email='johndoe@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'johndoe@example.com',
            'password': 'dog'
        }, follow_redirects=True)
        self.assertMessageFlashed(message='Invalid email or password.', category='danger')
        self.assert_template_used('auth/login.html')

    def test_register_and_confirmation(self):
        # register a new account
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john.doe',
            'password': 'cat',
            'first_name': 'john',
            'last_name': 'doe',
        })
        self.assertTrue(response.status_code == 302)

        # login with the new account
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        self.assert200(response)
        self.assert_template_used('auth/unconfirmed.html')

    def test_account_confirmation(self):
        # Create two users for testing
        u1 = User(username='jane.doe', email='jane.doe@example.com', password='testpw')
        u2 = User(username='john.doe', email='john.doe@example.com', password='testpw')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        user1 = User.query.filter_by(email='john.doe@example.com').first()
        user2 = User.query.filter_by(email='jane.doe@example.com').first()
        token1 = user1.generate_confirmation_token()
        token2 = user2.generate_confirmation_token()

        # Login user1
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john.doe@example.com',
            'password': 'testpw'
        }, follow_redirects=True)

        # Test invalid token supply generates flashed message
        response = self.client.get(url_for('auth.confirm', token=token2),
                                   follow_redirects=True)
        self.assert_message_flashed(message='The confirmation link is invalid or has expired.'
                                    , category='danger')
        self.assert_template_used('public/index.html')

        # Test valid confirmation token confirms user
        response = self.client.get(url_for('auth.confirm', token=token1),
                                   follow_redirects=True)
        self.assertTrue(
            b'You have confirmed your account' in response.data)

        # Test unconfirmed page no longer catches user
        response = self.client.get(url_for('auth.unconfirmed'), follow_redirects=True)
        self.assert_template_used('public/index.html')

    def test_account_already_confirmed(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(username='john.doe').first()
        token = user.generate_confirmation_token()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john.doe@example.com',
            'password': 'testpw'
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertMessageFlashed('Your account has already been confirmed.', 'success')

    def test_account_confirmation_email_resend(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(username='john.doe').first()
        token = user.generate_confirmation_token()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john.doe@example.com',
            'password': 'testpw'
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.resend_confirmation'), follow_redirects=True)
        self.assertMessageFlashed('A new confirmation email has been sent to your email address.', 'info')
        self.assert_template_used('public/index.html')

    def test_resgister_existing_email(self):
        u = User(email='johndoe@example.com', username='john.doe')
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.register'), data={
            'email': 'johndoe@example.com',
            'username': 'john.doe',
            'password': 'cat',
            'first_name': 'john',
            'last_name': 'doe',
        })
        self.assert_message_flashed(message='Email is already registered. Please enter a '
                                            'different email address or recover your password '
                                            'for your existing account to proceed.', category='danger')
        self.assert_template_used('auth/register.html')

    def test_resgister_existing_username(self):
        u = User(email='johndoe1@example.com', username='john.doe1')
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.register'), data={
            'email': 'johndoe2@example.com',
            'username': 'john.doe1',
            'password': 'cat',
            'first_name': 'john',
            'last_name': 'doe',
        })
        self.assert_message_flashed(message='Username already taken.  Please enter a different '
                                            'username or recover your password for your existing '
                                            'account to proceed.', category='danger')
        self.assert_template_used('auth/register.html')

    def test_logout_success(self):
        u = User(email='johndoe@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'johndoe@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assert_message_flashed(message='Successfully logged out.', category='success')

    def test_reset_password_unaccesible_to_logged_in_user(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john.doe@example.com',
            'password': 'testpw'
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.reset_password_request'), follow_redirects=True)
        self.assert_template_used('public/index.html')

    def test_reset_password_request_successful(self):
        # Reset password template gets rendered on get
        response = self.client.get(url_for('auth.reset_password_request'), follow_redirects=True)
        self.assert_template_used('auth/reset_password_request.html')

        # Reset password email gets sent
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.reset_password_request'), data={
            'email': 'john.doe@example.com'}, follow_redirects=True)
        self.assertMessageFlashed('An email with instructions for resetting your password has been sent to you.',
                                  'info')

    def test_reset_password_for_inactive_user(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True, active=False)
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.reset_password_request'), data={
            'email': 'john.doe@example.com'}, follow_redirects=True)
        self.assertMessageFlashed('That user account is no longer active.', 'danger')
        self.assertTemplateUsed('auth/reset_password_request.html')

    def test_reset_password_for_user_does_not_exist(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.reset_password_request'), data={
            'email': 'john.doe2@example.com'}, follow_redirects=True)
        self.assertMessageFlashed('A user account with that password does not exist. Please enter a '
                                  'valid email address.', 'danger')
        self.assertTemplateUsed('auth/reset_password_request.html')

    def test_logged_in_user_cannot_request_password_reset_by_email(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john.doe@example.com',
            'password': 'testpw'
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.reset_password', token='sampletoken'),
                                   follow_redirects=True)
        self.assertTemplateUsed('public/index.html')

    def test_successful_password_reset_form_render(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john.doe@example.com').first()
        token = user.generate_reset_token()
        response = self.client.get(url_for('auth.reset_password_request', token=token),
                                   follow_redirects=True)
        self.assertTemplateUsed('auth/reset_password_request.html')

    def test_password_reset_for_invalid_email(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john.doe@example.com').first()
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.reset_password', token=token), data={
            'email': 'foo.bar@example.com', 'password': 'testpw2', 'password': 'testpw2'}, follow_redirects=True)
        self.assertMessageFlashed('That does not appear to be a valid email.', 'danger')

    def test_valid_password_reset_post(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john.doe@example.com').first()
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.reset_password', token=token), data={
            'email': 'john.doe@example.com', 'password': 'testpw2', 'password': 'testpw2'}, follow_redirects=True)
        self.assertMessageFlashed('Your password has been reset.', 'success')

    def test_invalid_userid_in_password_reset_token(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        u2 = User(username='jane.doe', email='jane.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()
        user = User.query.filter_by(email='jane.doe@example.com').first()
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.reset_password', token=token), data={
            'email': 'john.doe@example.com', 'password': 'testpw2', 'password2': 'testpw2'}, follow_redirects=True)
        self.assertMessageFlashed('There was an error resetting your password.', 'danger')

    def test_render_password_reset_template(self):
        u = User(username='john.doe', email='john.doe@example.com', password='testpw', confirmed=True)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john.doe@example.com').first()
        token = user.generate_reset_token()
        response = self.client.get(url_for('auth.reset_password', token=token), follow_redirects=True)
        self.assertTemplateUsed('auth/reset_password.html')

    def test_last_seen_ping_on_login(self):
        u = User(email='johndoe@example.com', password='cat', confirmed=True)
        db.session.add(u)
        db.session.commit()
        response = self.client.post(url_for('auth.login'), data={
            'email': 'johndoe@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        user = User.query.filter_by(email='johndoe@example.com').first()
        last_seen = user.last_seen
        self.assertTrue(last_seen)
