from flask import g, jsonify, current_app, url_for, current_app
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_principal import Identity, UserNeed, RoleNeed, identity_changed
from app import sa
from app.security import AppPermissionNeed
from ..models import User, Role, AnonymousUser, EmailAddress
from . import api
from .errors import unauthorized, ValidationError as APIValidationError, forbidden
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
        raise APIValidationError("No email provided for login.")
    user = sa.session.query(User).join(EmailAddress).filter(EmailAddress._active == True).filter(
        EmailAddress._email == str(email).upper().strip()).first()
    if user is None:
        raise APIValidationError("Email provided does not match an active account")
    if not user.verify_password(password):
        return False
    if not user.confirmed:
        raise APIValidationError("User account is unconfirmed")
    if not user.active:
        raise APIValidationError("User account is inactive")
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
    # Test deserialization of token
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        raise APIValidationError("Token is expired.")
    except BadSignature:
        raise APIValidationError("Token is invalid.")
    # Extract user from valid token
    user = User.verify_api_auth_token(token)
    # CCheck if user is returned from token
    if user is None:
        raise APIValidationError("Token is invalid.")
    # User must be confirmed
    if not user.confirmed:
        raise APIValidationError("User account is unconfirmed.")
    # Set global request context g.current_user variable which is used in API routes
    setattr(g, 'current_user', user)
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
    return True


@token_auth.error_handler
def token_error():
    """Return a 401 error to the client."""
    r = jsonify({'error': 'authentication required'})
    r.headers['Location'] = url_for('api.new_token')
    r.headers['WWW-Authenticate'] = 'Bearer realm="Authentication Required"'
    r.status_code = 401
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


# def set_identity_permissions(user):
#     # Set the identity user object
#     identity = Identity(user.id)
#     identity.user = user
#     # Add the UserNeed to the identity
#     if hasattr(user, 'id'):
#         identity.provides.add(UserNeed(user.id))
#     # Update the identity with the roles that the user provides
#     if hasattr(user, 'role_id'):
#         role = Role.query.filter_by(id=user.role_id).first()
#         identity.provides.add(RoleNeed(role.name))
#         app_permissions = role.app_permissions
#         for app_permission_name in app_permissions:
#             identity.provides.add(AppPermissionNeed(str(app_permission_name)))
#     # Manually set global request context g variable for identity since session is not loaded
#     g.identity.provides = identity.provides
