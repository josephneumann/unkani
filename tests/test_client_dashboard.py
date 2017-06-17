from flask import url_for, g
from flask_login import current_user
from app import sa
from app.models import User
from tests.test_client_utils import BaseClientTestCase, user_dict
from datetime import datetime


class DashboardViewsFormsTestCase(BaseClientTestCase):
    def test_change_password(self):
        with self.client:
            # Create test user and login
            self.create_test_user()
            user = self.get_test_user()
            self.login()

            # Create change password request
            new_pw = 'testpw2'
            response = self.client.post(url_for('dashboard.change_password', userid=current_user.id), data={
                'old_password': user_dict.get('password'),
                'password': new_pw,
                'password2': new_pw
            }, follow_redirects=True)
            self.assert200(response)
            self.assertMessageFlashed(category='success')

            # Test new password
            self.assertTrue(current_user.verify_password(new_pw))

            # Test password change timestamp and hash archive was updated
            self.assertIsNotNone(current_user.last_password_hash)
            self.assertIsNotNone(current_user.password_timestamp)

    def test_password_change_invalid_password(self):
        with self.client:
            # Create test user and login
            self.create_test_user()
            self.login()
            new_pw = 'testpw2'

            # Test invalid password entry for password change
            response = self.client.post(url_for('dashboard.change_password', userid=current_user.id), data={
                'old_password': 'foobar',
                'password': new_pw,
                'password2': new_pw
            }, follow_redirects=True)
            self.assert200(response)
            self.assertMessageFlashed(category='danger')
            self.assertTrue(current_user.verify_password(user_dict.get('password')))

    def test_password_change_mis_matched_passwords(self):
        with self.client:
            # Create test user and login
            self.create_test_user()
            self.login()

            # Test mis-matched new password entry
            response = self.client.post(url_for('dashboard.change_password', userid=current_user.id), data={
                'old_password': user_dict.get('password'),
                'password': 'foobar1',
                'password2': 'foobar2'
            }, follow_redirects=True)
            self.assert200(response)
            self.assertMessageFlashed(category='danger')
            self.assertFalse(current_user.verify_password(user_dict.get('password')))

    def test_change_email_request_success(self):
        self.create_test_user()
        with self.client:
            # Test successful email change request
            self.login()
            new_email = 'JOHN.DOE2@EXAMPLE.COM'
            response = self.client.post(url_for('dashboard.change_email_request', userid=current_user.id), data={
                'new_email': new_email,
                'new_email2': new_email,
                'password': user_dict.get('password')
            }, follow_redirects=True)
            self.assert200(response)
            self.assertMessageFlashed(category='success')

    def test_change_email_request_wrong_password(self):
        self.create_test_user()
        with self.client:
            # Try passing an invalid password
            self.login()
            new_email2 = 'JOHN.DOE3@EXAMPLE.COM'
            response = self.client.post(url_for('dashboard.change_email_request', userid=current_user.id), data={
                'new_email': new_email2,
                'new_email2': new_email2,
                'password': 'foobar'
            }, follow_redirects=False)
            # self.assert200(response)
            self.assertMessageFlashed(category='danger')

    def test_change_email_request_existing_email(self):
        self.create_test_user()
        self.create_test_user(username='JANE.DOE', email='JANE.DOE@EXAMPLE.COM')
        with self.client:
            # Try registering an existing email
            self.login()
            existing_email = 'JANE.DOE@EXAMPLE.COM'
            response = self.client.post(url_for('dashboard.change_email_request', userid=current_user.id), data={
                'new_email': existing_email,
                'new_email2': existing_email,
                'password': user_dict.get('password')}, follow_redirects=True)

            self.assert200(response)
            self.assertMessageFlashed(category='danger')

    def test_change_email_token_success(self):
        with self.client:
            self.create_test_user()
            self.login()
            new_email = 'JOHN.DOE2@EXAMPLE.COM'
            response = self.client.post(url_for('dashboard.change_email_request', userid=current_user.id), data={
                'new_email': new_email,
                'new_email2': new_email,
                'password': user_dict.get('password')
            }, follow_redirects=True)
            token = current_user.generate_email_change_token(new_email)
            response = self.client.get(url_for('dashboard.change_email', token=token), follow_redirects=True)
            self.assertMessageFlashed(category='success')
            self.assertTrue(current_user.email.email.upper() == new_email.upper())

    def test_change_email_invalid_token(self):
        with self.client:
            self.create_test_user()
            self.login()
            new_email = 'JOHN.DOE2@EXAMPLE.COM'
            response = self.client.post(url_for('dashboard.change_email_request', userid=current_user.id), data={
                'new_email': new_email,
                'new_email2': new_email,
                'password': user_dict.get('password')
            }, follow_redirects=True)
            token = current_user.generate_email_change_token('JANE.DOE@EXAMPLE.COM')
            response = self.client.get(url_for('dashboard.change_email', token=token), follow_redirects=True)
            self.assertFalse(current_user.email.email.upper() == new_email.upper())

    def test_user_profile_update_success(self):
        with self.client:
            self.create_test_user()
            self.login()

            current_date = datetime.now().date()
            response = self.client.post(url_for('dashboard.user_profile', userid=current_user.id), data={
                'first_name': 'john',
                'last_name': 'doe',
                'username': 'john.doe',
                'dob': current_date,
                'phone': '253-506-8888'
            }, follow_redirects=True)
            self.assertMessageFlashed(category='success')
            self.assertTrue(current_user.dob == current_date)

    def test_user_profile_invalid_update_existing_username(self):
        with self.client:
            self.create_test_user()
            self.create_test_user(username='JANE.DOE', email='JANE.DOE@EXAMPLE.COM')
            self.login()
            current_date = datetime.now().date()
            response = self.client.post(url_for('dashboard.user_profile', userid=current_user.id), data={
                'first_name': 'john',
                'last_name': 'doe',
                'username': 'jane.doe',
                'dob': current_date,
                'phone': '253-506-8888'
            }, follow_redirects=True)
            self.assertMessageFlashed(category='danger')
            self.assertTrue(current_user.username.lower() == 'john.doe')

    def test_unable_to_access_user_profile_of_another_user(self):
        with self.client:
            self.create_test_user()
            self.create_test_user(username='JANE.DOE', email='JANE.DOE@EXAMPLE.COM')
            u2 = User.query.filter_by(_username='JANE.DOE').first()
            self.login()
            response = self.client.get(url_for('dashboard.user_profile', userid=int(u2.id)))
            self.assertRedirects(response, url_for('dashboard.user_profile', userid=current_user.id))
            self.assertMessageFlashed(category='danger')

    def test_unable_to_access_user_profile_of_none_user(self):
        with self.client:
            self.create_test_user()
            self.login()
            response = self.client.get(url_for('dashboard.user_profile', userid=9999), follow_redirects=True)
            self.assert404(response)
            self.assertMessageFlashed(category='danger')
