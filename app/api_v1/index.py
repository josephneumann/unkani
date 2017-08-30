from flask import request, jsonify, g, url_for
from . import api
from .utils import etag
from .authentication import token_auth


@api.route('/', methods=['GET'])
@token_auth.login_required
@etag
def index():
    response = jsonify({'versions':
                            {'v1':
                                 {'users': url_for('api_v1.get_users', _external=True)}
                             }
                        })
    response.status_code = 200
    return response
