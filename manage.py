#!/usr/bin/env python
import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include=['app/*'], omit=['app/utils.py', 'app/flask_sendgrid.py'])
    COV.start()

from app import create_app, db, mail
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app.utils import reset_db_command_line

# Create app with create_app class defined in __init__.py  test
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


# Create custom context with Flask-Script and set default import objects
# To create/upgrade the databases:
# $ python manage.py db migrate --m "Commit comment"
# $ python manage.py db upgrade
# $ heroku run python manage.py db upgrade --app unkani-staging
# $ heroku run python manage.py db upgrade --app unkani

# To recreate database from scratch
# Drop all tables in postgres db console
# $ heroku run python manage.py db downgrade base --app unkani
# $ heroku run python manage.py db upgrade head --app unkani


# To run as a shell:
# $ python manage.py shell
def make_shell_context():
    return dict(app=app, db=db, mail=mail, User=User, Role=Role)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def refresh_db():
    """Wipe db and reset with command line options
    for configuring admin user and random users"""
    reset_db_command_line()

@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, User
    # migrate database to latest revision
    upgrade()
    # create user roles
    Role.initialize_roles()


if __name__ == '__main__':
    manager.run()
