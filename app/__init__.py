# Application factory and primary Flask initialization and app generation
from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from config import config

#Intialize Flask extensions, but do not specify application instance
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

#Application factory function
#Use app.config.from_object method to pull config dict / object
def create_app(config_name):
    app = Flask(__name__)
    #Captures config from env variable, looks up dict object
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

#Complete initialization of app objects after config
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

#Register blueprint object with application object
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

