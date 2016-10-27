import os

#Define base configuration class for configuration settings that are shared
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfwznel2805lkd43o98udnj'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 465 #587 for TLS
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[unkani]'
    FLASKY_MAIL_SENDER = 'unkani admin <unkani@gmail.com>'
    UNKANI_ADMIN = os.environ.get('UNKANI_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_USER_ATTRS = ['username', 'first_name', 'last_name', 'email']

#Define an init_app class method that allows for config specific initialization
    @staticmethod
    def init_app(app):
        pass

#Define specific configuration variables as Config subclasses
class DevelopmentConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class StagingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

#Configuration objects are assigned to a dict for access in intitialization script from objects
config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
