from flask import request, abort, jsonify, g, url_for

from ..models import User
from .authentication import token_auth, basic_auth
from . import api


# @api.route('/users', methods=['GET'])
# def get_user_list():
#     """
#     Return list of users.
#     This endpoint requires basic auth and will return a list of user IDs.
#     """
#     users = User.query.order_by(User.id.asc())
#     if request.args.get('last_seen'):
#         users = users.filter(
#             User.last_seen > int(request.args.get('last_seen')))
#     return jsonify({'users': [user.to_dict() for user in users.all()]})


@api.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    """
    Return a user.
    This endpoint requires basic auth and will return a JSON user object requested by ID.
    """
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


    # @api.route('/users', methods=['POST'])
    # def new_user():
    #     """
    #     Register a new user.
    #     This endpoint is publicly available.
    #     """
    #     user = User.create(request.get_json() or {})
    #     if User.query.filter_by(nickname=user.nickname).first() is not None:
    #         abort(400)
    #     db.session.add(user)
    #     db.session.commit()
    #     r = jsonify(user.to_dict())
    #     r.status_code = 201
    #     r.headers['Location'] = url_for('api.get_user', id=user.id)
    #     return r

    # @api.route('/users/<id>', methods=['PUT'])
    # @token_auth.login_required
    # def edit_user(id):
    #     """
    #     Modify an existing user.
    #     This endpoint is requires a valid user token.
    #     Note: users are only allowed to modify themselves.
    #     """
    #     user = User.query.get_or_404(id)
    #     if user != g.current_user:
    #         abort(403)
    #     user.from_dict(request.get_json() or {})
    #     db.session.add(user)
    #     db.session.commit()
    #     return '', 204
    # Contact GitHub API Training Shop Blog About
    # © 2016 GitHub, Inc. Terms Privacy Security Status Help
