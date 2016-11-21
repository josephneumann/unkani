import os

#Define base configuration class for configuration settings that are shared
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfwznel2805lkd43o98udnj'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    #Old Flask_Mail Gmail Settings
    #MAIL_SERVER = 'smtp.googlemail.com'
    #MAIL_PORT = 465 #587 for TLS
    #MAIL_USE_TLS = False
    #MAIL_USE_SSL = True
    #MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'app.unkani@gmail.com'
    #MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    #FLASKY_MAIL_SUBJECT_PREFIX = '[unkani]'
    #FLASKY_MAIL_SENDER = 'unkani admin <unkani@gmail.com>'
    UNKANI_ADMIN = os.environ.get('UNKANI_ADMIN') or 'admin@unkani.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_USER_ATTRS = ['username', 'first_name', 'last_name', 'email']
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
    SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
    SENDGRID_DEFAULT_FROM = 'admin@unkani.com'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')

#Define an init_app class method that allows for config specific initialization
    @staticmethod
    def init_app(app):
        pass

#Define specific configuration variables as Config subclasses
class DevelopmentConfig(Config):
    DEBUG = True
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

class StagingConfig(Config):
    DEBUG = True
    TESTING = True
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

#Configuration objects are assigned to a dict for access in intitialization script from objects
config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
