from flask import g, jsonify, current_app, url_for
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, ValidationError as APIValidationError, forbidden
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()
multi_auth = MultiAuth(basic_auth, token_auth)


@api.before_request
def before_request():
    pass


@basic_auth.verify_password
def verify_password(email, password):
    if not email:
        return False
    user = User.query.filter_by(email=email).first()
    if user is None:
        return False
    if not user.confirmed:
        raise APIValidationError("User account is unconfirmed.")
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
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        raise APIValidationError("Token is expired.")
    except BadSignature:
        raise APIValidationError("Token is invalid.")
    user = User.verify_api_auth_token(token)
    if not user.confirmed:
        raise APIValidationError("User account is unconfirmed.")
    if user is None:
        raise APIValidationError("Token is invalid.")
    g.current_user = user
    return True


@token_auth.error_handler
def token_error():
    """Return a 401 error to the client."""
    r = jsonify({'error': 'authentication required'})
    r.headers['Location'] = url_for('api.new_token')
    r.headers['WWW-Authenticate'] = 'Bearer realm="Authentication Required"'
    r.status_code = 401
    return r
