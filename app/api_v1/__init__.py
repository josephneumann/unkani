from flask import Blueprint

api = Blueprint('api_v1', __name__)
from . import authentication, errors, utils
from .errors import *
from .index import *
from app.api_v1.resources import *
from app.api_v1.fhir import *