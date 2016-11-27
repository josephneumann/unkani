from flask import url_for
from flask_testing import TestCase
from flask_login import current_user
from app import db, create_app as create_application
from app.models import User, Role
from datetime import datetime, date


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

    def test_change_password_success(self):
        with self.client:
            u = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)

            response = self.client.post(url_for('dashboard.change_password'), data={
                'old_password': 'cat',
                'password': 'dog',
                'password2': 'dog'
            }, follow_redirects=True)
            self.assertMessageFlashed('Your password has been changed.', 'success')
            self.assertTrue(current_user.verify_password('dog'))

    def test_change_password_invalid_request(self):
        with self.client:
            u = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)

            response = self.client.post(url_for('dashboard.change_password'), data={
                'old_password': 'invalidpassword',
                'password': 'dog',
                'password2': 'dog'
            }, follow_redirects=True)
            self.assertMessageFlashed('You entered an invalid password.', 'danger')
            self.assertTrue(current_user.verify_password('cat'))
            self.assertTemplateUsed('dashboard/change_password.html')

    def test_change_email_request_success(self):
        with self.client:
            u = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            response = self.client.post(url_for('dashboard.change_email_request'), data={
                'new_email': 'johndoe2@gmail.com',
                'new_email2': 'johndoe2@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            db.session.remove()
            self.assertMessageFlashed('A confirmation email  has been sent to your new email.','info')

    def test_change_invalid_change_email_request_existing_email(self):
        with self.client:
            u = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            response = self.client.post(url_for('dashboard.change_email_request'), data={
                'new_email': 'johndoe@gmail.com',
                'new_email2': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            self.assertMessageFlashed('Email is already registered.','warning')

    def test_change_invalid_change_email_request_wrong_password(self):
        with self.client:
            u = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            response = self.client.post(url_for('dashboard.change_email_request'), data={
                'new_email': 'johndoe2@gmail.com',
                'new_email2': 'johndoe2@gmail.com',
                'password': 'invalidpassword'
            }, follow_redirects=True)
            self.assertMessageFlashed('Invalid password.','danger')

    def test_change_email_token_success(self):
        with self.client:
            u = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            token = current_user.generate_email_change_token('johndoe2@gmail.com')
            response = self.client.get(url_for('dashboard.change_email', token=token), follow_redirects=True)
            self.assertMessageFlashed('Your email has been updated.','success')
            self.assertEqual(current_user.email, 'johndoe2@gmail.com')

    def test_invalid_change_email_token(self):
        with self.client:
            u1 = User(email='johndoe@gmail.com', password='cat', confirmed=True)
            u2 = User(email='janedoe@gmail.com', password='cat', confirmed=True)
            db.session.add(u1)
            db.session.add(u2)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            user2 = User.query.filter_by(email='janedoe@gmail.com').first()
            token = user2.generate_email_change_token('janedoe2@gmail.com')
            response = self.client.get(url_for('dashboard.change_email', token=token), follow_redirects=True)
            self.assertMessageFlashed('Invalid email change request.','danger')

    def test_user_profile_update_success(self):
        with self.client:
            u = User(email='johndoe@gmail.com', username='john.doe', password='cat', confirmed=True)
            db.session.add(u)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            current_date = datetime.now().date()
            response = self.client.post(url_for('dashboard.user_profile'), data={
                'first_name': 'john',
                'last_name': 'doe',
                'username': 'john.doe',
                'dob': current_date,
                'phone': '222-888-9988'
            }, follow_redirects=True)
            db.session.remove()
            self.assertMessageFlashed('Your profile has been updated.', 'success')
            self.assertEqual(current_user.first_name, 'john')
            self.assertEqual(current_user.last_name, 'doe')
            self.assertEqual(current_user.dob, current_date)
            self.assertEqual(current_user.phone, '222-888-9988')

    def test_user_profile_invalid_update_existing_username(self):
        with self.client:
            u = User(email='johndoe@gmail.com', username='john.doe', password='cat', confirmed=True)
            u2 = User(email='janedoe@gmail.com', username='jane.doe', password='cat', confirmed=True)
            db.session.add(u)
            db.session.add(u2)
            db.session.commit()
            response = self.client.post(url_for('auth.login'), data={
                'email': 'johndoe@gmail.com',
                'password': 'cat'
            }, follow_redirects=True)
            current_date = datetime.now().date()
            response = self.client.post(url_for('dashboard.user_profile'), data={
                'first_name': 'john',
                'last_name': 'doe',
                'username': 'jane.doe',
                'dob': current_date,
                'phone': '222-888-9988'
            }, follow_redirects=True)
            db.session.remove()
            self.assertMessageFlashed('The username jane.doe is already taken. We kept your username the same.', 'danger')