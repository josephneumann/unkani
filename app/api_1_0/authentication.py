from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()
multi_auth = MultiAuth(basic_auth, token_auth)


# @api.before_request
# def before_request():
#     print("before request executed")
#     if not g.current_user.confirmed:
#         return forbidden('Unconfirmed account')


@basic_auth.verify_password
def verify_password(email, password):
    if not email:
        return False
    user = User.query.filter_by(email=email).first()
    if user is None:
        return False
    if user.verify_password(password):
        g.current_user = user
        return True


@basic_auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@token_auth.verify_token
def verify_token(token):
    """Token verification callback."""
    if not token:
        return False
    user = User.verify_api_auth_token(token)
    if user is None:
        return False
    g.current_user = user
    return True


@token_auth.error_handler
def token_error():
    """Return a 401 error to the client."""
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})
