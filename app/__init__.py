# Application factory and primary Flask initialization
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
#Import config object [which is itself a dict of config objects] from config package
from config import config

#Intialize Flask extensions, but do not specify application instance
# Since no application instance to initialize flask extensions with,
# we create them uninitialized by passing no arguments into their constructors.
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

#Application factory function
#Use Flask's app.config.from_object method to pull config object
#The configuration name is pulled from env variable and then that is
#Used as a key for accessing config dict's configuration object

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

#Complete initialization of extension objects with the app object
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

#Register blueprint objects with application object
#These MUST be imported last, to avoid circular dependencies in the blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

