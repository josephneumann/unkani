from flask import jsonify, url_for
from app.api_v1 import api_bp
from app.api_v1.utils.etag import etag


@api_bp.route('/', methods=['GET'])
@etag
def index():
    response = jsonify(
        {'resources': {'fhir': {'CodeSystem': url_for('api_v1.get_codesystems',
                                                      _external=True),
                                'ValueSet': url_for('api_v1.get_valuesets', _external=True),
                                'Patient': url_for('api_v1.patient_search', _external=True)},
                       'unkani': {'User': url_for('api_v1.get_users', _external=True)}},
         'authentication': url_for('api_v1.new_token', _external=True)
         }
    )
    response.status_code = 200
    return response
