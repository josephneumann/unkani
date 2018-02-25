# Application factory and primary Flask initialization
import logging
import os

from flask import Flask
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_moment import Moment
from flask_principal import Principal
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from raven.contrib.flask import Sentry
from redis import Redis

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
ma = Marshmallow()
moment = Moment()

default_redis_url = 'redis://localhost:6379'
redis = Redis.from_url(url=os.environ.get('REDIS_URL', default_redis_url))


# Application factory function
# Use Flask's app.config.from_object method to pull config object
# The configuration name is pulled from env variable and then that is
# Used as a key for accessing config dict's configuration object

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config.update(SESSION_REDIS=redis)

    # Check app config to see if SERVER_SESSION is set to True
    # If so, initialize flask-session.Session which defaults to session type set in
    # SESSION_TYPE config, which is for Unkani, 'redis'.  Sessions are stored on redis default port.

    config[config_name].init_app(app)

    if not app.config['SSL_DISABLE']:  # pragma: no cover
        from flask_sslify import SSLify
        sslify = SSLify(app)

    # Complete initialization of extension objects with the app object
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    sentry.init_app(app, logging=True, level=logging.ERROR)
    Principal(app, use_sessions=True)
    ma.init_app(app)
    moment.init_app(app)
    if app.config.get('SERVER_SESSION'):
        Session(app)

    # Register blueprint objects with application object
    # These MUST be imported last, to avoid circular dependencies in the blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .dashboard import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint, url_prefix='/app')

    from .api_v1 import api_bp as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1')

    return app
