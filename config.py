import os


# Define base configuration class for configuration settings that are shared
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfwznel2805lkd43o98udnj'

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UNKANI_ADMIN = os.environ.get('UNKANI_ADMIN_EMAIL') or 'app.unkani@gmail.com'
    UNKANI_ADMIN_EMAIL = os.environ.get('UNKANI_ADMIN_EMAIL')
    UNKANI_ADMIN_PASSWORD = os.environ.get('UNKANI_ADMIN_PASSWORD')

    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_USER_ATTRS = ['username', 'first_name', 'last_name', 'email']

    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
    SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
    SENDGRID_DEFAULT_FROM = 'admin@unkani.com'

    SERVER_SESSION = True
    SESSION_TYPE = 'redis'

    REDIS_URL = os.environ.get('REDIS_URL')
    BROKER_TRANSPORT = 'redis',

    # Define an init_app class method that allows for config specific initialization
    @staticmethod
    def init_app(app):
        pass


# Define specific configuration variables as Config subclasses
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    EMAIL_OFF = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SSL_DISABLE = True
    SENTRY_DISABLE = True
    USE_RATE_LIMITS = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    EMAIL_OFF = True
    SSL_DISABLE = True
    SENTRY_DISABLE = True
    USE_RATE_LIMITS = False
    SERVER_SESSION = False


class StagingConfig(Config):
    DEBUG = False
    TESTING = False
    EMAIL_OFF = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SSL_DISABLE = False
    SENTRY_DISABLE = False
    USE_RATE_LIMITS = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    EMAIL_OFF = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SSL_DISABLE = False
    SENTRY_DISABLE = False
    USE_RATE_LIMITS = False
    SERVER_SESSION = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


# Configuration objects are assigned to a dict for access in initialization script from objects
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
