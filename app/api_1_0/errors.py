from flask import jsonify
from . import api
from ..main.errors import forbidden, page_not_found, internal_server_error, ValidationError


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
