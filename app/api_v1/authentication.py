from flask import g, jsonify, url_for, current_app
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_principal import Identity, identity_changed
from app import db
from ..models import User, EmailAddress
from . import api
from app.api_v1.errors import unauthorized, AuthenticationError
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()
multi_auth = MultiAuth(basic_auth, token_auth)


@api.before_request
def before_request():  # pragma: no cover
    pass


@basic_auth.verify_password
def verify_password(email, password):
    if not email:
        raise AuthenticationError("No email address provided for login.")
    user = db.session.query(User).join(EmailAddress).filter(EmailAddress.active == True).filter(
        EmailAddress.email == str(email).upper().strip()).first()
    if user is None:
        raise AuthenticationError("Email provided does not match an active account")
    if not user.verify_password(password):
        return False
    if not user.confirmed:
        raise AuthenticationError("User account is unconfirmed")
    if not user.active:
        raise AuthenticationError("User account is inactive")
    setattr(g, 'current_user', user)
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
    return True


@basic_auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@token_auth.verify_token
def verify_token(token):
    """Token verification callback.  Sets user identity and permissions for request."""
    # Check is token exists
    if not token:
        return False
    # Extract user from valid token
    user = User.verify_api_auth_token(token)
    # Check if user is returned from token
    if user is None:
        raise AuthenticationError("Token is invalid.")
    # User must be confirmed
    if not user.confirmed:
        raise AuthenticationError("User account is unconfirmed.")
    # Set global request context g.current_user variable which is used in API routes
    # Since sessions are not used in RESTapi, there should not be any authentication info stored in session with
    # flask-login's login_user function
    setattr(g, 'current_user', user)
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
    return True


@token_auth.error_handler
def token_error():
    """Return a 401 error to the client.py."""
    r = unauthorized(message='Token authentication required.')
    r.headers['Location'] = url_for('api_v1.new_token')
    r.headers['WWW-Authenticate'] = 'Bearer realm="Authentication Required"'
    return r


@api.route('/tokens', methods=['POST'])
@basic_auth.login_required
def new_token():
    """
    Request a user token.
    This endpoint requires basic auth with email and password
    for a confirmed account
    This endpoint returns a Timed JSON Web Signature token
    """
    token = g.current_user.generate_api_auth_token()
    return jsonify({'token': token})


@api.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    db.session.commit()
