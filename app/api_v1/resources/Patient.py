from flask import request, url_for

from app.api_v1.authentication import token_auth
from app.api_v1.errors.user_errors import *
from app.api_v1.utils.rate_limit import rate_limit
from app.api_v1.utils.etag import etag
from app.api_v1.utils.bundle import create_bundle
from app.api_v1.utils.search import fhir_search
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
# @api_bp.route('/fhir/Patient/_search', methods=['POST']) #TODO better support for webform params
@token_auth.login_required
@enforce_fhir_mimetype_charset
@rate_limit(limit=5, period=15)
@etag
def patient_search():
    # Initialize a query that will be added to dynamically according to url params
    query = Patient.query
    # Define additional search support beyond the standard _id and _lastUpdated attributes
    model_support = {'active': {'ordered': False,
                                'modifier': ['not'],
                                'prefix': [],
                                'model': Patient,
                                'column': 'active',
                                'type': 'bool',
                                'validation': []},
                     'deceased': {'ordered': False,
                                  'modifier': ['not'],
                                  'prefix': [],
                                  'model': Patient,
                                  'column': 'deceased',
                                  'type': 'bool',
                                  'validation': []},
                     'birthdate': {'ordered': True,
                                   'modifier': [],
                                   'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                   'model': Patient,
                                   'column': 'dob',
                                   'type': 'date',
                                   'validation': []},
                     'death-date': {'ordered': True,
                                    'modifier': [],
                                    'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                    'model': Patient,
                                    'column': 'deceased_date',
                                    'type': 'date',
                                    'validation': []},
                     'given': {'ordered': False,
                               'modifier': ['exact', 'contains', 'missing'],
                               'prefix': [],
                               'model': Patient,
                               'column': 'first_name',
                               'type': 'string',
                               'validation': []}
                     }
    # Parse the request args and execute the search.  Return un-executed query
    query = fhir_search(args=request.args, model_support=model_support, base=Patient, query=query)
    # Pass the query to be executed to bundle/pagination utility
    bundle = create_bundle(query=query, paginate=True)

    # Create the response from bundle JSON
    response = jsonify(bundle.as_json())
    response.status_code = 200
    return response


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
