from flask import request, jsonify, g, url_for

from app import sa
from app.flask_sendgrid import send_email
from app.security import *
from . import api
from .authentication import token_auth
from .errors import forbidden
from ..models import User, user_schema, user_schema_create, user_schema_update


@api.route('/users', methods=['GET'])
@token_auth.login_required
@app_permission_userprofileupdate.require(http_exception=403)
def get_user_list():
    """
    Returns list of user ids and the user object's location.
    """
    user_results = User.query.order_by(User.id.asc())
    user_list = {}
    for user in user_results:
        if not g.current_user.has_access_to_user_operation(user=user):
            pass
        else:
            user_list[user.id] = url_for('api.get_user', userid=user.id, _external=True)
    return jsonify(user_list)


@api.route('/users/<int:userid>', methods=['GET'])
@token_auth.login_required
def get_user(userid):
    """
    Return a user.
    This endpoint requires basic auth and will return a JSON user object requested by ID.
    """
    user = User.query.get_or_404(userid)
    user_data = user_schema.dump(user)
    result = jsonify(user_data.data)
    result.headers['Location'] = url_for('api.get_user', userid=user.id)
    return result


@api.route('/users', methods=['POST'])
@token_auth.login_required
def new_user():
    """
    Register a new user
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "User could not be created",
                        "message": "Request JSON was improperly formatted."}), 422
    user, errors = user_schema_create.load(json_data)
    if errors:
        return jsonify({"error": "User could not be created",
                        "message": errors}), 422
    sa.session.add(user)
    sa.session.commit()
    result = user_schema.dump(user)
    json_result = jsonify({"message": "Created new user.",
                           "user": result.data})
    json_result.headers['Location'] = url_for('api.get_user', userid=user.id)
    return json_result, 201


@api.route('/users/<int:userid>', methods=['PUT', 'PATCH'])
@token_auth.login_required
def edit_user(userid):
    """
    Update or ovewrite an existing user
    This endpoint is requires a valid user token.
    Users are only allowed to modify themselves unless given the appropriate permission
    Returns a JSON reponse with user data, errors if they exist and a list of ignored fields
    Location header on the response indicates location of user record
    """
    user = User.query.get_or_404(userid)
    if not g.current_user.has_access_to_user_operation(user=user, other_permissions=[app_permission_userdelete]):
        forbidden("You do not have permission to update the user profile for user with id {}".format(userid))
    additional_message = None
    allowed_fields = ['email', 'username', 'first_name', 'last_name', 'password', 'dob', 'phone', 'description']
    if app_permission_userforceconfirmation.can():
        allowed_fields += ['confirmed']
    if app_permission_userdeactivate.can():
        allowed_fields += ['active']
    if app_permission_userrolechange.can():
        allowed_fields += ['role_id']
    original_email = user.email.email
    data = request.get_json()
    data['id'] = userid
    errors = user_schema_update.validate(data)
    if errors:
        return jsonify({"error": "User could not be updated",
                        "message": errors}), 422
    if 'email' in data and User.query.filter(user.email.email == data['email'], User.id != data['id']).first():
        return jsonify({"error": "User could not be updated",
                        "message": "A user with email {} already exists".format(data['email'])}), 422
    if 'username' in data and User.query.filter(User.username == data['username'], User.id != data['id']).first():
        return jsonify({"error": "User could not be updated",
                        "message": "A user with username {} already exists".format(data['username'])}), 422
    unallowed_fields = [{}]
    for key in data:
        if key != 'id' and key in allowed_fields:
            setattr(user, key, data[key])
        elif key != 'id':
            unallowed_fields[0][key] = data[key]
    if user.email.email.lower() != original_email.lower():
        user.confirmed = False
        token = user.generate_email_change_token(user.email.email.lower())
        send_email(subject='Unkani - Email Change', to=[user.email.email.lower()], template='auth/email/change_email',
                   token=token, user=user)
        additional_message = {
            "email changed": "The user's email has been changed to {} and requires confirmation via email".format(
                user.email.email)}
    sa.session.add(user)
    sa.session.commit()
    updated_user = user_schema.dump(User.query.get(userid))

    response = {"message": "User successfully updated",
                "user": updated_user.data}
    if additional_message:
        response.update(additional_message)
    if unallowed_fields[0]:
        ignored_message = {"ignored fields": unallowed_fields}
        response.update(ignored_message)
    json_response = jsonify(response)
    json_response.headers['Location'] = url_for('api.get_user', userid=user.id)
    return json_response, 200


@api.route('/users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    """
    Delete an existing user
    """
    user = User.query.get_or_404(int(id))
    if not g.current_user.has_access_to_user_operation(user=user, other_permissions=[app_permission_userdelete]):
        forbidden("You do not have permission to delete user with id {}".format(user.id))
    sa.session.delete(user)
    sa.session.commit()
    json_response = jsonify({"message": "User {} deleted".format(user.email.email)})
    return json_response, 200
