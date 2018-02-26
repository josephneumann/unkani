from flask import request, url_for

from app.api_v1.authentication import token_auth
from app.api_v1.errors.user_errors import *
from app.api_v1.utils.rate_limit import rate_limit
from app.api_v1.utils.etag import etag
from app.api_v1.utils.bundle import create_bundle
from app.api_v1.utils.search import parse_fhir_search
from app.api_v1.utils.requests import enforce_fhir_mimetype_charset
from app.models.fhir.patient import Patient


@api_bp.route('/fhir/Patient/<int:id>', methods=['GET'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_read(id):
    """
    Return a FHIR STU 3.0 Patient resource as JSON.
    """
    pt = Patient.query.get_or_404(ident=id)
    data = pt.dump_fhir_json()
    response = jsonify(data)
    response.headers['Location'] = url_for('api_v1.patient_read', id=pt.id)
    response.headers['Content-Type'] = 'application/fhir+json'
    response.status_code = 200
    return response


@api_bp.route('/fhir/Patient/<int:id>', methods=['PUT'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_update(id):
    pt = Patient.query.get_or_404(ident=id)
    return jsonify('Patient update: Coming Soon!')


@api_bp.route('/fhir/Patient/<int:id>', methods=['DELETE'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
def patient_delete(id):
    pt = Patient.query.get_or_404(ident=id)
    return jsonify('Patient delete: Coming Soon!')


@api_bp.route('/fhir/Patient', methods=['POST'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
def patient_create():
    return jsonify('Patient create: Coming Soon!')


@api_bp.route('/fhir/Patient/<int:id>/_history/<int:vid>', methods=['GET'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_vread(id, vid):
    pt = Patient.query.get_or_404(ident=id)
    return jsonify('Patient version read: Coming Soon!')


@api_bp.route('/fhir/Patient', methods=['GET'])
@api_bp.route('/fhir/Patient/_search', methods=['POST'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
def patient_search():
    query = Patient.query
    model_support = {}
    fhir_search_spec = parse_fhir_search(args=request.args, model_support=model_support)

    for key in fhir_search_spec.keys():
        if key == '_id':
            column = getattr(Patient, 'id')
            search_params = fhir_search_spec.get(key)
            op = search_params.get('op')
            query = query.filter(getattr(column, op)(search_params.get('value')))

        if key == '_lastUpdated':
            column = getattr(Patient, 'updated_at')
            search_params = fhir_search_spec.get(key)
            op = search_params.get('op')
            query = query.filter(getattr(column, op)(search_params.get('value')))

    bundle = create_bundle(query=query, paginate=True)
    response = jsonify(bundle.as_json())
    response.status_code = 200
    return response

    # Accept GET with URL parameters
    # Accept POST with application/x-www-form-urlencoded submission
    # Return 200 status code if successful with a Bundle resource type = searchset
    # If search succeeds but no records returned, still 200 status code
    # 4XX or 5XX status code for other errors
    # If desired, a successful search can return an OperationOutcome object with Bundle.entry.search.mode = outcome
    # No operation outcome is allowed for 400 / 500 errors.  No entries in OperationOutcome fatal or error


@api_bp.route('/fhir/Patient/$match', methods=['POST'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_op_match():
    return jsonify('Patient matching operation: Coming Soon!')


@api_bp.route('/fhir/Patient/$everything', methods=['POST'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@enforce_fhir_mimetype_charset
@etag
def patient_op_everything():
    pt = Patient.query.get_or_404(ident=id)
    return jsonify('Patient everything operation: Coming Soon!')
