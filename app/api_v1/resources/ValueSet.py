from app.api_v1.authentication import token_auth
from app.api_v1.errors.errors import *
from app.api_v1.utils.rate_limit import rate_limit
from app.api_v1.utils.etag import etag
from app.models.fhir.codesets import ValueSet


@api_bp.route('/fhir/ValueSet/<string:resource_id>', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def get_valueset(resource_id):
    """
    Return a FHIR ValueSet resource as JSON.
    """
    valueset = ValueSet.query.filter(ValueSet.resource_id == resource_id).first_or_404()
    data = valueset.dump_fhir_json()
    response = jsonify(data)
    response.headers['Location'] = url_for('api_v1.get_valueset', resource_id=valueset.resource_id)
    response.status_code = 200
    return response


@api_bp.route('/fhir/ValueSet', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def get_valuesets():
    """
    Return FHIR ValueSet resources as JSON.
    """
    return jsonify('Coming Soon!')
