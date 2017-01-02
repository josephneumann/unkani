# Application factory and primary Flask initialization
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal
from raven.contrib.flask import Sentry
import logging
from celery import Celery
import os
from config import config, Config

# Import config object [which is itself a dict of config objects] from config package
from config import config

# Intialize Flask extensions, but do not specify application instance
# Since no application instance to initialize flask extensions with,
# we create them uninitialized by passing no arguments into their constructors.
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = 'You must log in to view this page.'
login_manager.login_message_category = 'info'
sentry = Sentry()
celery = Celery(__name__, broker=os.environ.get('CELERY_BROKER_URL', 'redis://'),
                backend=os.environ.get('CELERY_BROKER_URL', 'redis://'))

from .flask_sendgrid import send_async_email


# Application factory function
# Use Flask's app.config.from_object method to pull config object
# The configuration name is pulled from env variable and then that is
# Used as a key for accessing config dict's configuration object

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    if not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    # Complete initialization of extension objects with the app object
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    sentry.init_app(app, logging=True, level=logging.ERROR)
    celery.conf.update(app.config)
    Principal(app)

    # Register blueprint objects with application object
    # These MUST be imported last, to avoid circular dependencies in the blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .dashboard import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint, url_prefix='/app')

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app