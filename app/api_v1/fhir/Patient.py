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
def get_patient(id):
    """
    Return a FHIR STU 3.0 Patient resource as JSON.
    """
    pt = Patient.query.filter(Patient.id == id).one_or_none()
    if not pt:
        return not_found()
    else:
        data = pt.dump_fhir_json()
        response = jsonify(data)
        response.headers['Location'] = url_for('api_v1.get_patient', id=pt.id)
        response.status_code = 200
        return response
