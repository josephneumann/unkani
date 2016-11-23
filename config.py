import os


# Define base configuration class for configuration settings that are shared
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfwznel2805lkd43o98udnj'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
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
    BROKER_URL = CELERY_BROKER_URL
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT=['json']
    BROKER_TRANSPORT = 'redis'
    CELERY_IMPORTS = ['app.flask_sendgrid']

    # Define an init_app class method that allows for config specific initialization
    @staticmethod
    def init_app(app):
        pass


# Define specific configuration variables as Config subclasses
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TESTING_DATABASE_URL')
    WTF_CSRF_ENABLED = False

class StagingConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


# Configuration objects are assigned to a dict for access in intitialization script from objects
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
