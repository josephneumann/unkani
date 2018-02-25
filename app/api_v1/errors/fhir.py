from app.api_v1 import api_bp
from app.api_v1.errors.exceptions import *
from flask import jsonify, url_for
from app.api_v1.utils.operation_outcome import create_operation_outcome
from werkzeug.http import HTTP_STATUS_CODES


def fhir_error_response(status_code, outcome_list):
    if status_code not in HTTP_STATUS_CODES:
        raise ValueError('The status code {} is not a recognized HTTP status code.'.format(status_code))
    oo = create_operation_outcome(outcome_list=outcome_list)
    response = jsonify(oo.as_json())
    response.status_code = status_code
    return response


@api_bp.errorhandler(AuthenticationError)
def authentication_error_handler(e):
    response = fhir_error_response(status_code=401, outcome_list=[
        {'severity': 'error', 'type': 'security', 'location': [url_for('api_v1.new_token', _external=True)],
         'diagnostics': e.args[0], 'details': 'Basic authentication error: {}'.format(e.args[0])}])
    response.headers['Location'] = url_for('api_v1.new_token', _external=True)
    response.headers['WWW-Authenticate'] = 'Basic'
    return response


@api_bp.errorhandler(BasicAuthError)
def basic_auth_error_handler(e):
    response = fhir_error_response(status_code=401, outcome_list=[
        {'severity': 'error', 'type': 'login', 'location': [url_for('api_v1.new_token', _external=True)],
         'diagnostics': e.args[0], 'details': 'Basic authentication error: {}'.format(e.args[0])}])
    response.headers['Location'] = url_for('api_v1.new_token', _external=True)
    response.headers['WWW-Authenticate'] = 'Basic'
    return response


@api_bp.errorhandler(TokenAuthError)
def token_auth_error_handler(e):
    response = fhir_error_response(status_code=401, outcome_list=[
        {'severity': 'error', 'type': 'login', 'location': [url_for('api_v1.new_token', _external=True)],
         'diagnostics': e.args[0], 'details': 'Bearer token auth error: {}'.format(e.args[0])}])
    response.headers['Location'] = url_for('api_v1.new_token', _external=True)
    response.headers['WWW-Authenticate'] = 'Bearer'
    return response


@api_bp.errorhandler(TokenExpiredError)
def token_expired_error_handler(e):
    response = fhir_error_response(status_code=401, outcome_list=[
        {'severity': 'error', 'type': 'expired', 'location': [url_for('api_v1.new_token', _external=True)],
         'diagnostics': e.args[0], 'details': 'Authentication token expired: complete authentication for new token'}])
    response.headers['Location'] = url_for('api_v1.new_token', _external=True)
    response.headers['WWW-Authenticate'] = 'Bearer'
    return response


@api_bp.errorhandler(RateLimitError)
def too_many_requests(e):
    response = fhir_error_response(status_code=429, outcome_list=[
        {'severity': 'error', 'type': 'throttled',
         'diagnostics': e.args[0], 'details': 'Too many requests: Rate-limit exceeded'}])
    for header in ['X-RateLimit-Remaining', 'X-RateLimit-Limit', 'X-RateLimit-Reset']:
        response.headers[header] = e.args[0].get(header)
    return response


@api_bp.errorhandler(400)
def bad_request_handler(e):
    response = fhir_error_response(status_code=400, outcome_list=[
        {'severity': 'error', 'type': 'invalid',
         'diagnostics': str(e), 'details': 'Bad request from client'}])
    return response


@api_bp.errorhandler(BadRequestError)
def bad_request_error_handler(e):
    response = fhir_error_response(status_code=400, outcome_list=[
        {'severity': 'error', 'type': 'invalid',
         'diagnostics': str(e.args[0]), 'details': 'Bad Request: {}'.format(str(e.args[0]))}])
    return response


@api_bp.errorhandler(403)
def forbidden_handler(e):
    response = fhir_error_response(status_code=403, outcome_list=[
        {'severity': 'error', 'type': 'forbidden',
         'diagnostics': str(e), 'details': 'Forbidden'}])
    return response


@api_bp.errorhandler(ForbiddenError)
def forbidden_error_handler(e):
    response = fhir_error_response(status_code=403, outcome_list=[
        {'severity': 'error', 'type': 'forbidden',
         'diagnostics': str(e.args[0]), 'details': 'Forbidden: {}'.format(str(e.args[0]))}])
    return response


@api_bp.errorhandler(404)
def not_found_handler(e):
    response = fhir_error_response(status_code=404, outcome_list=[
        {'severity': 'fatal', 'type': 'not-found',
         'diagnostics': str(e), 'details': 'Resource not found'}])
    return response


@api_bp.errorhandler(405)
def method_not_allowed_handler(e):
    response = fhir_error_response(status_code=405, outcome_list=[
        {'severity': 'fatal', 'type': 'not-found',
         'diagnostics': str(e), 'details': 'Method not allowed'}])
    return response


@api_bp.errorhandler(500)
def internal_server_error_handler(e):
    response = fhir_error_response(status_code=500, outcome_list=[
        {'severity': 'fatal', 'type': 'exception',
         'diagnostics': str(e), 'details': 'An internal error has occurred'}])
    return response


@api_bp.errorhandler(NotModifiedError)
def not_modified_handler(e):
    response = fhir_error_response(status_code=304, outcome_list=[
        {'severity': 'error', 'type': 'business-rule',
         'diagnostics': str(e), 'details': 'The requested resource was not modified'}])
    return response


@api_bp.errorhandler(PreconditionFailedError)
def not_modified_handler(e):
    response = fhir_error_response(status_code=412, outcome_list=[
        {'severity': 'error', 'type': 'business-rule',
         'diagnostics': str(e), 'details': 'Precondition failed'}])
    return response
