import unittest
import time

from app.models import User
from app import db

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
        u = User(password ='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password ='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password ='cat')
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
        self.assertTrue(u.reset_password(token, 'dog')) #Test token vlaue matches userid
        self.assertTrue(u.verify_password('dog')) #Test new password is dog


    def test_invalid_reset_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_valid_email_change_token(self):
        test_email='johndoe@gmail.com'
        u = User(email=test_email)
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('johndoe@aol.com')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.verify_last_email(test_email))

    def text_invalid_email_change_token(self):
        email1 = 'johdoe@gmail.com'
        email2 = 'janedoe@gmail.com'
        u1 = User(email=email1)
        u2 = User(email=email2)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        email3 = 'johndoe@aol.com'
        token = u1.generate_email_change_token(email3)
        self.assertFalse(u2.change_email(token))
        self.assertFalse(u2.verify_email(email3))