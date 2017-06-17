from flask import url_for
from flask_testing import TestCase
from app import sa, create_app as create_application
from app.models import User, Role, AppPermission

# Default user information for testing authentication
user_dict = dict(email="JOHN.DOE@EXAMPLE.COM",
                 username="JOHN.DOE",
                 password="testpw",
                 first_name="JOHN",
                 last_name="DOE",
                 confirmed=True)


# Common setup, teardown and utility methods to be re-used with each test module
# Subclasses flask_testings TestCase, which is itself a subclass of unittest.TestCase
class BaseClientTestCase(TestCase):
    # Default render templates to True
    render_templates = True

    def create_app(self):
        app = create_application('testing')
        return app

    def setUp(self):
        sa.drop_all()
        sa.create_all()
        AppPermission.initialize_app_permissions()
        Role.initialize_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        sa.session.remove()
        sa.drop_all()
        sa.create_all()

    def login(self, email=user_dict.get("email"), password=user_dict.get("password")):
        return self.client.post(url_for('auth.login'), data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get(url_for('auth.logout'), follow_redirects=True)

    def create_test_user(self, username=user_dict.get("username"),
                         email=user_dict.get("email"),
                         password=user_dict.get("password"),
                         confirmed=user_dict.get("confirmed"),
                         first_name=user_dict.get("first_name"),
                         last_name=user_dict.get("last_name"),
                         ):
        u = User(username=username, email=email, password=password, confirmed=confirmed, first_name=first_name,
                 last_name=last_name)
        sa.session.add(u)
        sa.session.commit()

    def get_test_user(self, username=user_dict.get("username")):
        return User.query.filter_by(_username=username.upper()).first()

    # Improve the assertMessageFlashed method
    def assertMessageFlashed(self, message=None, category=None):
        """
            Custom validator for flashed messages that improves on Flask-Testing
            implementation of the same method.
            
            Checks if a given message was flashed.
            Only works if your version of Flask has message_flashed
            signal support (0.10+) and blinker is installed.
            
            Changes from flask-testing implementation:
            1) Allows checking of category only by leaving param 'method' = None
            2) Allows checking of message only by leaving param 'category' = None
            3) Renders flashed message in error message for easier debugging
            4) All category and message equivalence checks are done with lower() and strip() string methods

            :param message: expected message
            :param category: expected message category
            """
        try:
            import blinker
            _is_signals = True

        except ImportError:  # pragma: no cover
            _is_signals = False

        try:
            from flask import message_flashed

            _is_message_flashed = True
        except ImportError:
            message_flashed = None
            _is_message_flashed = False

        if not _is_signals or not _is_message_flashed:
            raise RuntimeError("Your version of Flask doesn't support message_flashed."
                               "This requires Flask 0.10+ with signals support")

        if message:
            message = str(message).lower().strip()

        if category:
            category = str(category).lower().strip()

        for _message, _category in self.flashed_messages:
            if isinstance(_message, str):
                _message = _message.lower().strip()

            if isinstance(_category, str):
                _category = _category.lower().strip()

            if message is None and category is not None:
                if _category == category:
                    return True

            if category is None and message is not None:
                if _message == message:
                    return True

            if _message == message and _category == category:
                return True

            raise AssertionError(
                """Message '%s' in category '%s' wasn't flashed.

                MESSAGE FLASHED: %s 
                CATEGORY: %s""" % (message, category, _message, _category))
