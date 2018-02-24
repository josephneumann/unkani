from flask import Blueprint

api = Blueprint('api_v1', __name__)
from app.api_v1 import resources
from app.api_v1 import errors
from app.api_v1 import index