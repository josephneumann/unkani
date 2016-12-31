from flask import jsonify, g

from .. import db
from .authentication import basic_auth, token_auth, multi_auth
from . import api


@api.route('/tokens', methods=['POST'])
@basic_auth.login_required
def new_token():
    """
    Request a user token.
    This endpoint is requires basic auth with email and password
    This endpoint returns a Timed JSON Web Signature token
    """
    token = g.current_user.generate_api_auth_token()
    return jsonify({'token': token})
