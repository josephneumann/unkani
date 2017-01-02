from flask import request, abort, jsonify, g, url_for

from ..models import User
from .authentication import token_auth, basic_auth, multi_auth
from .errors import ValidationError
from . import api
from app import db


@api.route('/users/', methods=['GET'])
@multi_auth.login_required
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
        user_list[user.id] = user.username
    return jsonify(user_list)


@api.route('/users/<int:id>', methods=['GET'])
@multi_auth.login_required
def get_user(id):
    """
    Return a user.
    This endpoint requires basic auth and will return a JSON user object requested by ID.
    """
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())


@api.route('/users/', methods=['POST'])
def new_user():
    """
    Register a new user.
    """
    try:
        request_dict = dict(request.get_json())
    except:
        raise ValidationError("Invalid json payload")
    error_list = []
    if User.query.filter_by(email=request_dict['email']).first() is not None:
        error_list.append("Email is already in use.")
    if User.query.filter_by(username=request_dict['username']).first() is not None:
        error_list.append("Username is already in use.")
    if error_list:
        message = "Validation error(s) raised during user account creation: "
        for error in error_list:
            message += error + " "
        raise ValidationError(message)
    else:
        user = User.create(dict(request.get_json() or {}))
        db.session.add(user)
        db.session.commit()
        r = jsonify(user.to_dict())
        r.status_code = 201
        r.headers['Location'] = url_for('api.get_user', id=user.id)
        return r


@api.route('/users/<id>', methods=['PUT'])
@multi_auth.login_required
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
