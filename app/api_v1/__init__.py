from flask import Blueprint

api = Blueprint('api_v1', __name__)
from . import authentication
from . import users
from . import errors
from . import index