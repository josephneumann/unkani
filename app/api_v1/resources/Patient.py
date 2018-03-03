from flask import request, url_for

from app.api_v1.authentication import token_auth
from app.api_v1.errors.user_errors import *
from app.api_v1.utils.rate_limit import rate_limit
from app.api_v1.utils.etag import etag
from app.api_v1.utils.bundle import create_bundle
from app.api_v1.utils.search import fhir_search
from app.api_v1.utils.requests import enforce_fhir_mimetype_charset
from app.models.fhir.patient import Patient
from app.models.fhir.address import Address
from app.models.fhir.email_address import EmailAddress
from app.models.fhir.phone_number import PhoneNumber


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

    ##############################################################
    # Declare FHIR Search Parameters Supported
    ##############################################################
    model_support = {'active': {'modifier': ['not'],
                                'prefix': [],
                                'model': Patient,
                                'column': ['active'],
                                'type': 'bool'},
                     'deceased': {'modifier': ['not'],
                                  'prefix': [],
                                  'model': Patient,
                                  'column': ['deceased'],
                                  'type': 'bool'},
                     'birthdate': {'modifier': [],
                                   'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                   'model': Patient,
                                   'column': ['dob'],
                                   'type': 'date'},
                     'death-date': {'modifier': [],
                                    'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                    'model': Patient,
                                    'column': ['deceased_date'],
                                    'type': 'date'},
                     'given': {'modifier': ['exact', 'contains', 'missing'],
                               'prefix': [],
                               'model': Patient,
                               'column': ['first_name', 'middle_name'],  # Will search both with or condition
                               'type': 'string'},
                     'family': {'modifier': ['exact', 'contains', 'missing'],
                                'prefix': [],
                                'model': Patient,
                                'column': ['last_name'],
                                'type': 'string'},
                     'name': {'modifier': ['exact', 'contains', 'missing'],
                              'prefix': [],
                              'model': Patient,
                              'column': ['last_name', 'first_name', 'middle_name', 'suffix', 'prefix'],
                              'type': 'string'},
                     'gender': {'modifier': ['exact', 'contains', 'missing'],
                                'prefix': [],
                                'model': Patient,
                                'column': ['sex'],
                                'type': 'string'},
                     'address-city': {'modifier': ['exact', 'contains', 'missing'],
                                      'prefix': [],
                                      'model': Address,
                                      'column': ['city'],
                                      'type': 'string'},
                     'address-state': {'modifier': ['exact', 'contains', 'missing'],
                                       'prefix': [],
                                       'model': Address,
                                       'column': ['state'],
                                       'type': 'string'},
                     'address-postalcode': {'modifier': ['exact', 'contains', 'missing'],
                                            'prefix': [],
                                            'model': Address,
                                            'column': ['zipcode'],
                                            'type': 'string'},
                     'address-country': {'modifier': ['exact', 'contains', 'missing'],
                                         'prefix': [],
                                         'model': Address,
                                         'column': ['country'],
                                         'type': 'string'},
                     'address': {'modifier': ['exact', 'contains', 'missing'],
                                 'prefix': [],
                                 'model': Address,
                                 'column': ['address1', 'address2', 'city', 'state', 'zipcode', 'country'],
                                 'type': 'string'},
                     'email': {'modifier': ['exact', 'contains', 'missing'],
                               'prefix': [],
                               'model': EmailAddress,
                               'column': ['email'],
                               'type': 'string'},  # TODO validate email address w/ exact
                     'phone': {'modifier': ['exact', 'contains', 'missing'],
                               'prefix': [],
                               'model': PhoneNumber,
                               'column': ['number'],
                               'type': 'string'},  # TODO validate phone w/ exact
                     'language': {'modifier': ['exact', 'contains', 'missing'],
                                  'prefix': [],
                                  'model': Patient,
                                  'column': ['preferred_language'],
                                  'type': 'string'},
                     'identifier': {'modifier': ['exact', 'contains'],  # TODO: Support missing
                                    'prefix': [],
                                    'model': Patient,
                                    'column': {'http://unkani.com': 'uuid', 'http://hl7.org/fhir/sid/us-ssn': 'ssn'},
                                    'type': 'token'}  # TODO:  Validate SSN - match without hyphens
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
