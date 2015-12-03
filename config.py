import os
basedir = os.path.abspath(os.path.dirname(__file__))

"""
Define base configuration class for configuration settings that are shared
Then define a hierarchy of configuration classes that can be used for different environments"""
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfwznel2805lkd43o98udnj'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[unkani]'
    FLASKY_MAIL_SENDER = 'unkani admin <unkani@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

# Define an init_app class method that allows for config specific initialization
    @staticmethod
    def init_app(app):
        pass

#Define specific configuration variables as Config subclasses
class DevelopmentConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://JosephNeumann:rascal60276@localhost:5432/unkani'


class StagingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgres://vqcacoubeivowt:O-imkkMzZhDc2ObP5wSqt1eMsM@ec2-107-21-219-201.compute-1.amazonaws.com:5432/d142erar1mp2nr'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgres://jqipmfcikgmzvx:9ItJ3ZsSGLRfvf1AZmi3pAMnXA@ec2-107-21-223-72.compute-1.amazonaws.com:5432/dl78gbk5f6cmd'

#Different configurations are registered in a config dictionary.
config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
