#!/usr/bin/env python
import os
import subprocess
import sys

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include=['app/*'], omit=['app/utils.py', 'app/flask_sendgrid.py'])
    COV.start()

from app import create_app, db, mail
from app.models import User, Role, AppPermission
from flask_script import Manager, Shell, Command, prompt, prompt_bool
from flask_migrate import Migrate, MigrateCommand

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
    return dict(app=app, db=db, mail=mail, User=User, Role=Role, AppPermission=AppPermission)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


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
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, User, AppPermission
    # migrate database to latest revision
    upgrade()
    # create user roles
    AppPermission.initialize_app_permissions()
    Role.initialize_roles()
    User.initialize_admin_user()


@manager.command
def dbcreate():
    """Command line utility to drop / create database, initialize user, roles
    and permission models.  Create admin and random users """
    print(""""
    __________________________________________________________________________
    |                        !!!-----WARNING-----!!!                          |
    |This command drops all tables, re-creates them and initializes some data |
    |As a result ALL data will be lost from the target environment            |
    --------------------------------------------------------------------------

    """)
    if prompt_bool("Are you sure you want to proceed?", default=False):
        print('Database is refreshing...')
        if prompt_bool("Drop all tables first?", default=False):
            print('Dropping and recreating tables...')
            db.drop_all()
            print('Tables have been dropped...')
        print("Creating tables if needed...")
        db.create_all()
        print("Database tables created...")
        print()
        print("Initializing app permissions...")
        AppPermission.initialize_app_permissions()
        print("App permissions created...")
        print()
        print("Initializing user roles...")
        Role.initialize_roles()
        print("User roles created...")
        print()
        print("Creating admin user...")
        User.initialize_admin_user()
        print("Admin user created or updated...")
        print()

        if prompt_bool("Create randomly generated users?", default=True):
            user_create_number = prompt("How many random users do you want to create?: ", default=10)
            if not user_create_number:
                user_create_number = 10
            print("Creating " + str(user_create_number) + " random user(s)...")
            user_list = []
            while len(user_list) < int(user_create_number):
                user = User()
                user.randomize_user()
                user_list.append(user)
            db.session.add_all(user_list)
            db.session.commit()
            print()
            print("Created the following users:")
            for user in user_list:
                print(user.username)
            total_users = str(len(user_list))
            print()
            print("Total random users created: " + total_users)

        print("""
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        !Process completed without errors!
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """)
    else:
        print("Oh thank god............")
        print("That was a close call!")


if __name__ == '__main__':
    manager.run()
