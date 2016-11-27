import time
from flask_testing import TestCase
from app.models import User, Role, load_user
from app import db
from app import create_app as create_application
from datetime import datetime, timedelta


class UserModelTestCase(TestCase):
    def create_app(self):
        app = create_application('testing')
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()
        Role.initialize_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.create_all()

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
        u1 = User()
        db.session.add(u1)
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
        self.assertTrue(u.reset_password(token, 'dog'))  # Test token vlaue matches userid
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

    def test_valid_email_change_token_and_last_email_saved(self):
        test_email = 'johndoe@gmail.com'
        u = User(email=test_email)
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('johndoe@aol.com')
        self.assertTrue(u.change_email(token))

    def test_invalid_email_change_token_wrong_user(self):
        email1 = 'johdoe@gmail.com'
        email2 = 'janedoe@gmail.com'
        email3 = 'joedoe@gmail.com'
        u1 = User(email=email1)
        u2 = User(email=email2)
        u3 = User(email=email3)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
        email4 = 'johndoe@aol.com'
        u1_token = u1.generate_email_change_token(email4)
        u1_token_taken_email = u1.generate_email_change_token(email2)
        none_token = None
        self.assertFalse(u2.change_email(u1_token))
        self.assertFalse(u1.change_email(none_token))
        self.assertFalse(u1.change_email(u1_token_taken_email))

    def test_verify_last_email(self):
        test_email = 'johndoe@gmail.com'
        u = User(email=test_email)
        db.session.add(u)
        db.session.commit()
        new_email = 'johndoe@aol.com'
        token = u.generate_email_change_token(new_email)
        u.change_email(token)
        self.assertTrue(u.verify_last_email(test_email))
        self.assertFalse(u.verify_last_email(new_email))

    def test_verify_email(self):
        test_email = 'johndoe@gmail.com'
        u = User(email=test_email)
        db.session.add(u)
        db.session.commit()
        u = User.query.filter_by(email=test_email).first()
        new_email = 'johndoe@aol.com'
        self.assertTrue(u.verify_email(test_email))
        self.assertFalse(u.verify_email(new_email))

    def test_user_repr(self):
        username = 'testusername'
        u = User(username=username)
        db.session.add(u)
        db.session.commit()
        string_user = str(u)
        self.assertEqual(string_user, "<User 'testusername'>")
        self.assertNotEqual(string_user, "<User 'testusername2'>")

    def test_role_repr(self):
        r = Role.query.filter_by(name='User').first()
        string_role = str(r)
        self.assertEqual(string_role, "<Role 'User'>")
        self.assertNotEqual(string_role, "<User 'User2'>")

    def test_load_user(self):
        u = User(username='testuser')
        db.session.add(u)
        db.session.commit()
        u2 = load_user("1")
        self.assertEqual(u.username, u2.username)
        self.assertEqual(u.id, u2.id)

    def test_create_random_user_staticmethod(self):
        u = User()
        u.create_random_user()
        email = u.email
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email=email).first()
        self.assertTrue(user is not None)
        self.assertTrue(user.email is not None)
        self.assertTrue(user.phone is not None)
        self.assertTrue(user.first_name is not None)
        self.assertTrue(user.last_name is not None)
        self.assertTrue(user.dob is not None)
        self.assertTrue(user.active)
        self.assertFalse(user.confirmed)
        self.assertEqual(user.role_id, 1)

        # Pass through invalid gender and password
        u = User()
        u.create_random_user(gender='invalidgender', password='testpw')
        email = u.email
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email=email).first()
        self.assertTrue(user is not None)

    def test_random_dob(self):
        test_length = 50
        dob_list = []
        for x in range(0, test_length):
            user = User()
            dob_list.append(user.random_dob())
        self.assertEqual(len(dob_list), test_length)
        for x in range(0, test_length):
            dob = dob_list.pop(0)
            self.assertNotIn(dob, dob_list)
            self.assertLessEqual(dob, datetime.now().date() - timedelta(days=3 * 365))
            self.assertGreaterEqual(dob, datetime.now().date() - timedelta(days=101 * 365))

    def test_random_phone(self):
        phone_list = []
        test_length = 50
        for x in range(0, test_length):
            user = User()
            phone_list.append(user.random_phone())
        self.assertEqual(len(phone_list), test_length)
        for x in range(0, test_length):
            phone = phone_list.pop(0)
            self.assertNotIn(phone, phone_list)
            self.assertEqual(len(phone), 12)

    def test_initialize_roles_staticmethod(self):
        Role.initialize_roles()
        admin_role = Role.query.filter_by(id=0).first()
        user_role = Role.query.filter_by(id=1).first()
        self.assertTrue(admin_role is not None)
        self.assertEqual(admin_role.name, 'Admin')
        self.assertTrue(user_role.name, 'User')

