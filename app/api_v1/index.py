from flask import jsonify, url_for
from . import api
from app.api_v1.etag import etag
from .authentication import token_auth


@api.route('/', methods=['GET'])
@token_auth.login_required
@etag
def index():
    response = jsonify({'versions':
        {'v1':
            {
                'fhir': {'CodeSystem': url_for('api_v1.get_codesystems', _external=True),
                         'ValueSet': url_for('api_v1.get_valuesets', _external=True),
                         'Patient': url_for('api_v1.patient_search', _external=True)},
                'resources': {'User': url_for('api_v1.get_users', _external=True)}
            }
        }
    })
    response.status_code = 200
    return response
