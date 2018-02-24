from app.api_v1 import api
from app.api_v1.errors.exceptions import TokenExpiredError
from flask import jsonify, url_for
from app.api_v1.operation_outcome import create_operation_outcome


@api.errorhandler(TokenExpiredError)
def token_expired(e):
    oo = create_operation_outcome(outcome_list=[
        {'severity': 'error', 'type': 'expired', 'location': [url_for('api_v1.new_token', _external=True)],
         'diagnostics': e.args[0], 'details': 'Authentication token expired: complete authentication for new token'}])
    response = jsonify(oo.as_json())
    response.status_code = 401
    response.headers['Content-Type'] = 'application/fhir+json'
    response.headers['Charset'] = 'UTF-8'
    response.headers['Location'] = url_for('api_v1.new_token', _external=True)
    return response
