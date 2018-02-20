from flask import url_for, request

from app.api_v1.authentication import token_auth
from app.api_v1.errors import *
from app.api_v1.rate_limit import rate_limit
from app.api_v1.utils import etag
from app.api_v1.fhir.fhir_utils import create_bundle, parse_fhir_search, enforce_fhir_mimetype_charset
from app.models.fhir.patient import Patient


@api.route('/fhir/Patient/<int:id>', methods=['GET'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_read(id):
    """
    Return a FHIR STU 3.0 Patient resource as JSON.
    """
    pt = Patient.query.filter(Patient.id == id).one_or_none()
    if not pt:
        return not_found()
    else:
        data = pt.dump_fhir_json()
        response = jsonify(data)
        response.headers['Location'] = url_for('api_v1.patient_read', id=pt.id)
        response.headers['Content-Type'] = 'application/fhir+json'
        response.status_code = 200
        return response


@api.route('/fhir/Patient/<int:id>', methods=['PUT'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_update(id):
    return jsonify('Patient update: Coming Soon!')


@api.route('/fhir/Patient/<int:id>', methods=['DELETE'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
def patient_delete(id):
    return jsonify('Patient delete: Coming Soon!')


@api.route('/fhir/Patient/<int:id>', methods=['POST'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
def patient_create(id):
    return jsonify('Patient create: Coming Soon!')


@api.route('/fhir/Patient/<int:id>/_history/<int:vid>', methods=['GET'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_vread(id, vid):
    return jsonify('Patient version read: Coming Soon!')


@api.route('/fhir/Patient', methods=['GET'])
@api.route('/fhir/Patient/_search', methods=['POST'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
def patient_search():
    query = Patient.query
    fhir_search_spec = parse_fhir_search(args=request.args)
    search_support = {'_id': {'modifier': ['exact', 'not'],
                              'prefix': []},
                      '_lastUpdated': {'modifier': [],
                                       'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne']}
                      }

    for key in fhir_search_spec.keys():
        if key == '_id':
            column = getattr(Patient, 'id')
            search_params = fhir_search_spec.get(key)

            if search_params.get('modifier') in search_support[key]['modifier']:
                op = search_params.get('modifierOp')
            else:
                op = '__eq__'
                # TODO: Check if handing is strict and log error for un-supported modifier

            if search_params.get('prefix'):
                pass
                # TODO: If strict handling, reject any prefix values
            query = query.filter(getattr(column, op)(search_params.get('value')))

    bundle = create_bundle(query=query, paginate=True)
    response = jsonify(bundle.as_json())
    response.status_code = 200
    response.headers['Content-Type'] = 'application/fhir+json'
    response.headers['Charset'] = 'UTF-8'
    return response

    # Accept GET with URL parameters
    # Accept POST with application/x-www-form-urlencoded submission
    # Return 200 status code if successful with a Bundle resource type = searchset
    # If search succeeds but no records returned, still 200 status code
    # 4XX or 5XX status code for other errors
    # If desired, a successful search can return an OperationOutcome object with Bundle.entry.search.mode = outcome
    # No operation outcome is allowed for 400 / 500 errors.  No entries in OperationOutcome fatal or error


@api.route('/fhir/Patient/$match', methods=['POST'])
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_op_match():
    return jsonify('Patient matching operation: Coming Soon!')


@api.route('/fhir/Patient/$everything', methods=['POST'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@enforce_fhir_mimetype_charset
@etag
def patient_op_everything():
    return jsonify('Patient everything operation: Coming Soon!')
