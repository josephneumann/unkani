from flask import url_for

from app.api_v1.authentication import token_auth
from app.api_v1.errors import *
from app.api_v1.rate_limit import rate_limit
from app.api_v1.utils import etag
from app.models.fhir.patient import Patient


@api.route('/fhir/Patient/<int:id>', methods=['GET'])
@token_auth.login_required
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
        response.status_code = 200
        return response


@api.route('/fhir/Patient/<int:id>', methods=['PUT'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def patient_update(id):
    return jsonify('Patient update: Coming Soon!')


@api.route('/fhir/Patient/<int:id>', methods=['DELETE'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def patient_delete(id):
    return jsonify('Patient delete: Coming Soon!')


@api.route('/fhir/Patient/<int:id>', methods=['POST'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def patient_create(id):
    return jsonify('Patient create: Coming Soon!')


@api.route('/fhir/Patient/<int:id>/_history/<int:vid>', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def patient_vread(id, vid):
    return jsonify('Patient version read: Coming Soon!')


@api.route('/fhir/Patient', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def patient_search():
    return jsonify('Patient search: Coming Soon!')


@api.route('/fhir/Patient/$match', methods=['POST'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def patient_match():
    return jsonify('Patient matching operation: Coming Soon!')
