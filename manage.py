#!/usr/bin/env python3
import os
import subprocess
import sys

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include=['app/*'], omit=['app/flask_sendgrid.py'])
    COV.start()

from app import create_app, sa, mail
from app.models import *
from flask_script import Manager, Shell, Command, prompt, prompt_bool
from flask_migrate import Migrate, MigrateCommand

# Create app with create_app class defined in __init__.py  test
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, sa)


# Run python shell with application context
def make_shell_context():
    return dict(app=app, sa=sa, mail=mail, PhoneNumber=PhoneNumber, User=User, Role=Role, AppPermission=AppPermission,
                Patient=Patient,
                Address=Address, EmailAddress=EmailAddress)


manager.add_command("shell", Shell(make_context=make_shell_context))

# To create/upgrade the databases:
# $ python manage.py alembic migrate --m "Commit comment"
# $ python manage.py alembic upgrade
manager.add_command('alembic', MigrateCommand)


class CeleryWorkerStart(Command):
    """Starts the celery worker."""
    name = 'celery'
    capture_all_args = True

    def run(self, argv):
        ret = subprocess.call(
            ['celery', 'multi', 'start', 'worker1', '-A', 'celery_worker.celery'
                , '--loglevel=info', '--pidfile=/var/run/celery/%n.pid', '--logfile=/var/log/celery/%n%I.log'] + argv)
        sys.exit(ret)


manager.add_command("celery-start", CeleryWorkerStart())


class CeleryWorkerStop(Command):
    """Starts the celery worker."""
    name = 'celery'
    capture_all_args = True

    def run(self, argv):
        ret = subprocess.call(
            ['celery', 'multi', 'stopwait', 'worker1', '-A', 'celery_worker.celery'
                , '--loglevel=info', '--pidfile=/var/run/celery/%n.pid', '--logfile=/var/log/celery/%n%I.log'] + argv)
        sys.exit(ret)


manager.add_command("celery-stop", CeleryWorkerStop())


class CeleryWorkerRestart(Command):
    """Starts the celery worker."""
    name = 'celery'
    capture_all_args = True

    def run(self, argv):
        ret = subprocess.call(
            ['celery', 'multi', 'restart', 'worker1', '-A', 'celery_worker.celery'
                , '--loglevel=info', '--pidfile=/var/run/celery/%n.pid', '--logfile=/var/log/celery/%n%I.log'] + argv)
        sys.exit(ret)


manager.add_command("celery-restart", CeleryWorkerRestart())


class GunicornRunserver(Command):
    """Starts the application with the Gunicorn
    webserver on the localhost bound to port 5000"""

    name = 'gunicorn'
    capture_all_args = True

    def run(self, argv):
        ret = subprocess.call(
            ['gunicorn', '--bind', '0.0.0.0:5000', 'manage:app'] + argv)
        sys.exit(ret)


manager.add_command("gunicorn", GunicornRunserver())


@manager.command
def test(coverage=False):
    """
    Run the unit tests.
    Run with '--coverage' command to run coverage and
    output results as HTML report in /tmp/coverage/*
    """
    os.environ['FLASK_CONFIG'] = 'testing'
    app.config['TESTING'] = True
    app.login_manager.init_app(app)

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
def deploy():
    """Command line utility to complete deployment tasks:
     1) Drop all tables (optional)
     2) Upgrade to latest Alembic revision (optional)
     3) Create new tables if introduced in revision
     4) Initialize app permisions, user roles and admin user
     5) Create random users (optional) """
    if prompt_bool("Are you sure you want to proceed?", default=False):
        if prompt_bool("Upgrade to latest Alembic revision?", default=True):
            print()
            print("Upgrading to Alembic head revision if needed...")
            from flask_migrate import upgrade
            upgrade()
            print("Alembic revision up to date!")
            print()
        print("Initializing app permissions...")
        AppPermission.initialize_app_permissions()
        print("Initializing user roles...")
        Role.initialize_roles()
        print("Creating admin user...")
        User.initialize_admin_user()
        print()

        if prompt_bool("Create randomly generated users?", default=True):
            user_create_number = prompt("How many random users do you want to create?: ", default=10)
            if not user_create_number:
                user_create_number = 10
            print("Creating " + str(user_create_number) + " random user(s)...")
            user_list = []
            print("Generating a library of random demographics to use...")
            demo_list = random_demographics(number=int(user_create_number))
            print("Creating user objects...")
            print(user_create_number, end="...")
            while len(user_list) < int(user_create_number):
                user = User()
                user.randomize_user(demo_dict=demo_list.pop(0))
                user_list.append(user)
                print("{}".format(int(user_create_number) - len(user_list)), end='...', flush=True)
            print()
            print("Persisting objects to the database...")
            sa.session.add_all(user_list)
            sa.session.commit()
            total_users = str(len(user_list))
            print()
            print("Total random users created: " + total_users)

        if prompt_bool("Create randomly generated patients?", default=True):
            patient_create_number = prompt("How many random patients do you want to create?: ", default=10)
            if not patient_create_number:
                patient_create_number = 10
            print("Creating " + str(patient_create_number) + " random patient(s)...")
            patient_list = []
            print("Generating a library of random demographics to use...")
            demo_list = random_demographics(number=int(patient_create_number))
            print("Creating patient objects...")
            print(patient_create_number, end="...")
            while len(patient_list) < int(patient_create_number):
                pt = Patient()
                pt.randomize_patient(demo_dict=demo_list.pop(0))
                patient_list.append(pt)
                print("{}".format(int(patient_create_number) - len(patient_list)), end='...', flush=True)
            print()
            print("Persisting objects to the database...")
            sa.session.add_all(patient_list)
            sa.session.commit()
            total_patients = str(len(patient_list))
            print()
            print("Total random users created: " + total_patients)

        print("Process completed without errors.")
    else:
        print("Oh thank god............")
        print("That was a close call!")


if __name__ == '__main__':
    manager.run()
