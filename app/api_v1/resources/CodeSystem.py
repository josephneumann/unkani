from app.api_v1.authentication import token_auth
from app.api_v1.errors.user_errors import *
from app.api_v1.utils.rate_limit import rate_limit
from app.api_v1.utils.etag import etag
from app.models.fhir.codesets import CodeSystem
from flask import url_for


@api_bp.route('/fhir/CodeSystem/<string:resource_id>', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def get_codesystem(resource_id):
    """
    Return a FHIR CodeSystem resource as JSON.
    """
    codesystem = CodeSystem.query.filter(CodeSystem.resource_id == resource_id).first_or_404()
    data = codesystem.dump_fhir_json()
    response = jsonify(data)
    response.headers['Location'] = url_for('api_v1.get_codesystem', resource_id=codesystem.resource_id)
    response.status_code = 200
    return response

@api_bp.route('/fhir/CodeSystem', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def get_codesystems():
    """
    Return FHIR CodeSystem resources as JSON.
    """
    return jsonify('Coming Soon!')