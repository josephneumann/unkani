from flask import request, abort, jsonify, g, url_for
from ..models import User, user_schema, users_schema
from .authentication import token_auth, basic_auth, multi_auth
from .errors import ValidationError, forbidden
from . import api
from app import db
from app.security import app_permission_admin, create_user_permission

@api.route('/users', methods=['GET'])
@token_auth.login_required
def get_user_list():
    """
    Returns list of user ids and usernames.
    """
    user_results = User.query.order_by(User.id.asc())
    # if request.args.get('last_seen'):
    #     users = users.filter(
    #         User.last_seen > int(request.args.get('last_seen')))
    user_list = {}
    for user in user_results:
        user_list[user.id] = url_for('api.get_user', id=user.id)
    return jsonify(user_list)


@api.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    """
    Return a user.
    This endpoint requires basic auth and will return a JSON user object requested by ID.
    """
    user = User.query.get_or_404(id)
    user_data = user_schema.dump(user)
    result = jsonify(user_data.data)
    result.headers['Location'] = url_for('api.get_user', id=user.id)
    return result


@api.route('/users', methods=['POST'])
@token_auth.login_required
def new_user():
    """
    Register a new user
    """
    post_fields = ["username", "email", "password", "dob", "first_name", "last_name", "phone"]
    if g.current_user.has_admin_permission():
        admin_post_fields = ["role_id", "active", "confirmed"]
        for field in admin_post_fields:
            post_fields.append(field)
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Invalid JSON payload")
    data, errors = user_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    user_with_email = User.query.filter_by(email=data['email']).first()
    user_errors = []
    if user_with_email:
        user_errors.append("A user with the email {} already exists".format(user_with_email.email))
    user_with_username = User.query.filter_by(email=data['username']).first()
    if user_with_username:
        user_errors.append("A user with the username {} already exists".format(user_with_username.username))
    if user_errors:
        message = "Validation error(s) raised during user account creation: "
        for error in user_errors:
            message += error + " "
        raise ValidationError(message)
    user = User()
    for field in post_fields:
        if field in data:
            setattr(user, field, data.get(field))
    db.session.add(user)
    db.session.commit()
    result = user_schema.dump(User.query.get(user.id))
    json_result = jsonify({"message": "Created new user.",
                           "user": result.data})
    json_result.headers['Location'] = url_for('api.get_user', id=user.id)
    return json_result, 201


@api.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def edit_user(id):
    """
    Modify an existing user.
    This endpoint is requires a valid user token.
    Note: users are only allowed to modify themselves.
    """
    user = User.query.get_or_404(int(id))
    try:
        request_dict = dict(request.get_json())
    except:
        raise ValidationError("Invalid json payload")
    error_list = []
    email = request_dict.get("email")
    username = request_dict.get("username")
    error_list = []
    if email and email != user.email:
        if User.query.filter_by(email=request_dict['email']).first() is not None:
            error_list.append("Email is already in use.")
    if username and username != user.username:
        if User.query.filter_by(username=request_dict['username']).first() is not None:
            error_list.append("Username is already in use.")
    if error_list:
        message = "Validation error(s) raised during user account creation: "
        for error in error_list:
            message += error + " "
        raise ValidationError(message)
    for field in ['username', 'password', 'email', 'first_name', 'last_name']:
        try:
            setattr(user, field, request_dict[field])
        except:
            raise ValidationError("Error updating field: {}".format(field))
    db.session.add(user)
    db.session.commit()
    return '', 204

@api.route('/users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    """
    Delete an existing user
    """
    user = User.query.get_or_404(int(id))
    user_permission = create_user_permission(user.id)
    if not (app_permission_admin.can() or user_permission.can()):
        forbidden("You do not have permssion to delete user with id {}".format(user.id))
    db.session.delete(user)
    db.session.commit()
    json_response = jsonify({"message": "User {} deleted".format(user.email)})
    return json_response, 204


#PATCH