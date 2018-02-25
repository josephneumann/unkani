from flask import Blueprint

api_bp = Blueprint('api_v1', __name__)
from app.api_v1 import resources
from app.api_v1.errors.fhir_errors import *
from app.api_v1.errors.user_errors import *
from app.api_v1 import index
from app.api_v1 import request_hooks