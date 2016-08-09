#!/usr/bin/env python

import os
from app import create_app, db
from app.models import User, Role, Patient
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

#Create app with create_app class defined in __init__.py  test
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

#Create custom context with Flask-Script and set default import objects
# To create/upgrade the databases:
# $ python manage.py db migrate --m "Commit commet"
# $ python manage.py db upgrade
# $ heroku run python manage.py db upgrade --app unkani-staging
# $ heroku run python manage.py db upgrade --app unkani

#To recreate database from scratch
#Drop all tables in postgres db console
# $ heroku run python manage.py db downgrade base --app unkani
# $ heroku run python manage.py db upgrade head --app unkani


# To run as a shell:
# $ python manage.py shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
