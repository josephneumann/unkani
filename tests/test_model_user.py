import time
from tests.test_client_utils import BaseClientTestCase, user_dict
from app.models import User, Role, load_user
from app import db


class UserModelTestCase(BaseClientTestCase):

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_last_password_is_saved(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        u.password = 'dog'
        self.assertTrue(u.verify_password('dog'))
        self.assertTrue(u.verify_last_password('cat'))

    def test_users_created_in_db(self):
        u = User()
        db.session.add(u)
        db.session.commit()
        userlist = User.query.all()
        self.assertEqual(len(userlist), 1)

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))  # Test token value matches userid
        self.assertTrue(u.verify_password('dog'))  # Test new password is dog

    def test_invalid_reset_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_token()
        none_token = None
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertFalse(u2.reset_password(none_token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_verify_email(self):
        self.create_test_user()
        u = self.get_test_user()
        self.assertTrue(u.verify_email(user_dict.get('email')))
        self.assertFalse(u.verify_email('foobar'))

    def test_load_user(self):
        u = User(username='testuser')
        db.session.add(u)
        db.session.commit()
        u2 = load_user("1")
        self.assertEqual(u.username, u2.username)
        self.assertEqual(u.id, u2.id)

    def test_randomize_user(self):
        user = User()
        user.randomize_user()
        db.session.add(user)
        db.session.commit()
        self.assertTrue(user is not None)
        self.assertTrue(user.email is not None)
        self.assertTrue(user.phone_number.number is not None)
        self.assertTrue(user.first_name is not None)
        self.assertTrue(user.last_name is not None)
        self.assertTrue(user.dob is not None)
        self.assertTrue(user.active)
        self.assertFalse(user.confirmed)
        self.assertEqual(user.role.name, 'User')

    def test_initialize_roles_staticmethod(self):
        Role.initialize_roles()
        admin_role = Role.query.filter_by(name='Admin').first()
        super_admin_role = Role.query.filter_by(name='Super Admin').first()
        user_role = Role.query.filter_by(name='User').first()
        self.assertTrue(admin_role is not None)
        self.assertTrue(super_admin_role is not None)
        self.assertTrue(user_role is not None)
