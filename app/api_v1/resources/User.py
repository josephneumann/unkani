from flask import request, g
from sqlalchemy import or_, and_
from sqlalchemy.orm import aliased

from app import db
from app.models import Address, AppGroup, PhoneNumber, Role, EmailAddress
from app.models.user import User, UserAPI, UserVersionSchema
from app.security import *
from app.utils.demographics import *
from app.api_v1.authentication import token_auth
from app.api_v1.errors import *
from app.api_v1.rate_limit import rate_limit
from app.api_v1.utils import paginate_query, filter_ops, register_arg_error
from app.api_v1.etag import etag


@api.route('/User', methods=['GET'])
@token_auth.login_required
@app_permission_userprofileupdate.require(http_exception=403)
@rate_limit(limit=5, period=15)
@etag
def get_users():
    # TODO: Fix error that arises when passing filter=version_number,eq,1

    # Set variables for query to execute
    app_groups = g.current_user.app_groups
    app_group_ids = []
    for i in g.current_user.app_groups:
        app_group_ids.append(i.id)
    level = g.current_user.role.level
    id = g.current_user.id

    # Create a User model alias to be used with existence test in subquery
    ua = aliased(User, name='ua')

    # Return un-executed query that is pre-filtered for security
    query = User.query \
        .join(Role) \
        .filter(or_(Role.level < level, User.id == id)) \
        .join(EmailAddress) \
        .filter(and_(EmailAddress.primary == True, EmailAddress.active == True)) \
        .filter(db.session.query(ua) \
                .join(AppGroup, ua.app_groups) \
                .filter(AppGroup.id.in_(app_group_ids)) \
                .filter(User.id == ua.id).distinct().exists()
                )

    # initialize error list of dicts
    error_list = []

    # Check request args for a filter parameter, assign to var filter
    # format: ?filter=attribute,operator,value;attribute,operator,value
    # special case for 'in' operator:  ?filter=attribute,in,value1,value2,...valuen-1, valuen
    # ex: ?filter=last_name,eq,doe;first_name,in,john,jane
    filter_spec = request.args.get('filter')
    # If a filter arg exists, parse and handle as needed
    if filter_spec:
        # Filter args are ';' delimited if multiple filters.  Components of a filter are comma-delimited
        filters = [f.split(',') for f in filter_spec.split(';')]
        # filters = [['last_name', 'eq', 'doe'], ['first_name', 'in', 'john', 'jane']]
        for f in filters:
            # Check length of filter list.  If < 3, it is always invalid
            # If length >3 and the operator != 'in', then it is invalid
            # ['last_name', 'eq', 'doe']
            # ['first_name', 'in', 'john', 'jane']
            if len(f) < 3 or (len(f) > 3 and f[1] != 'in'):
                # This is an invalid filter and will be ignored.  Register filter attribute as error
                error_list.append(register_arg_error(arg=f, type='invalid filter argument'))
                continue
            # Handle in operator
            if f[1] == 'in':
                f = [f[0], f[1], f[2:]]
                # f = ['first_name', 'in', ['JOSEPH', 'AUDRA', 'KANICKI']]
            # Get shared dictionary of filter operations for validation
            ops = filter_ops
            try:
                # Lookup operator in operator dict
                op = ops[f[1]]
            except KeyError:
                # If lookup fails, register as an error and continue
                error_list.append(register_arg_error(arg=f[1], type='invalid filter argument operator'))
                continue
            # Once operator is confirmed, apply the filter values to SQLAlchemy ORM query
            else:
                # First Handle special cases that don't filter on a User model attribute like email
                # User email filter must be applied to joined EmailAddress object.
                if f[0] in ['email', 'email_address']:
                    column = getattr(EmailAddress, 'email')
                    if op == '__eq__':
                        try:
                            f[2] = validate_email(f[2])
                        except ValueError as e:
                            error_list.append(register_arg_error(
                                arg=e.args[0],
                                type='invalid filter argument'))
                            continue
                    else:
                        f[2] = str(f[2]).upper().strip()
                    # Update query with new filter
                    # Email join is completed in base query, since all accounts have emails
                    query = query.filter(getattr(column, op)(f[2]))

                # User phone number filter must be applied to joined PhoneNumber object.
                elif f[0] in ['phone', 'phone_number']:
                    column = getattr(PhoneNumber, 'number')
                    # If equality operator is used, make sure it is a valid phone to lookup
                    if op == '__eq__':
                        try:
                            f[2] = validate_phone(f[2])
                        except ValueError as e:
                            error_list.append(register_arg_error(
                                arg=e.args[0],
                                type='invalid filter argument'))
                            continue
                    # Otherwise, strip to numeric digits only for lookup with other operators
                    else:
                        f[2] = re.sub(r'[^0-9]', '', f[2])
                    query = query.join(PhoneNumber).filter(PhoneNumber.active == True).filter(
                        PhoneNumber.primary == True)
                    query = query.filter(getattr(column, op)(f[2]))

                # User address attribute filters must be applied to joined Address object.
                elif f[0] in ['address1', 'address2', 'city', 'state', 'zipcode']:
                    column = getattr(Address, f[0])
                    if op == '__eq__':
                        if f[0] == 'state':
                            try:
                                f[2] = validate_state(f[2])
                            except ValueError as e:
                                error_list.append(register_arg_error(
                                    arg=e.args[0],
                                    type='invalid filter argument'))
                                continue
                    else:
                        # Otherwise upper and trim argument for convenience
                        f[2] = str(f[2]).upper().strip()
                    query = query.join(Address).filter(Address.primary == True).filter(Address.active == True)
                    query = query.filter(getattr(column, op)(f[2]))

                # Otherwise assume filter on User model attribute.  Attempt column lookup
                elif hasattr(User, f[0]):
                    column = getattr(User, f[0])
                    # Proceed if the column is found on the model
                    if column:
                        # Help requester with case-normalization that is done in database for string attributes
                        if f[0] in ['first_name', 'last_name', 'username']:
                            f[0] = str(f[0]).upper().strip()
                        # Update query with new filter
                        query = query.filter(getattr(column, op)(f[2]))
                else:
                    # If filter argument attribute cannot be found on base model or in special cases
                    # Register as an error and ignore the filter
                    error_list.append(register_arg_error(arg=f[0], type='invalid filter argument'))
                    continue

    sort_spec = request.args.get('sort')
    if sort_spec:
        sort = [s.split(',') for s in sort_spec.split(';')]
        for s in sort:
            if len(s) == 2 and s[1] in ['asc', 'desc']:
                direction = s[1]
            else:
                direction = 'asc'
            if s[0] in ['email', 'email_address']:
                column = getattr(EmailAddress, 'email')
            elif hasattr(User, s[0]):
                column = getattr(User, s[0])
                if s[0] == 'id' and direction == 'asc':
                    continue
            else:
                error_list.append(register_arg_error(arg=s[0], type='invalid sort argument'))
                continue

            # If matching sort column is found, filter the query
            if column:
                query = query.order_by(getattr(column, direction)())
    else:
        query = query.order_by(User.id.asc())

    response = paginate_query(query=query, name='Users', error_list=error_list, max_per_page=50)
    return response


@api.route('/User/<int:userid>', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
@etag
def get_user(userid):
    """
    Return a user.
    This endpoint requires token auth and will return a JSON user object requested by ID.
    """
    user = User.query.get(userid)
    if not user:
        return not_found()
    else:
        data = user.dump()
        response = jsonify({'User': data, 'errors': []})
        response.headers['Location'] = url_for('api_v1.get_user', userid=user.id)
        response.status_code = 200
        return response


@api.route('/User', methods=['POST'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def new_user():
    """
    Register a new user
    """
    if not app_permission_usercreate.can():
        return forbidden(message='You do not have sufficient permissions to crete a new user.')
    json_data = request.get_json()
    uv = UserAPI()
    uv.loads_json(json_data)
    uv.run_validations()
    uv.run_permission_checks()
    user, errors = uv.make_object()
    if uv.errors['critical']:
        model_errors = process_model_errors(uv.errors)
        return generate_error_response(errors=model_errors, code=400)
    elif isinstance(user, User):
        db.session.add(user)
        db.session.commit()
        model_errors = process_model_errors(uv.errors)
        data = {"user": user.dump(), "errors": model_errors}
        response = jsonify(data)
        response.headers['Location'] = url_for('api_v1.get_user', userid=user.id)
        response.status_code = 201
        return response
    else:
        response = jsonify({'User': None, 'errors': {'critical': {'user creation': 'failed to create user'}}})
        response.status_code = 400
        return response


@api.route('/User/<int:userid>', methods=['PATCH'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def update_user(userid):
    """
    Update or overwrite an existing user
    This endpoint is requires a valid user token.
    Users are only allowed to modify themselves unless given the appropriate permission
    Returns a JSON reponse with user data, errors if they exist and a list of ignored fields
    Location header on the response indicates location of user record
    """
    # Lookup user by id, return NotFound error if missing
    user = User.query.get_or_404(userid)
    orig_email = user.email.email

    # Check app permission for logged in user to update the given user
    if not g.current_user.is_accessible(requesting_user=user, other_permissions=[app_permission_userprofileupdate]):
        forbidden(message="Permission denied: unable to update user.")

    # Deserialize JSON data and run validations
    json_data = request.get_json()
    uv = UserAPI()
    uv.user = user
    uv.loads_json(json_data)
    uv.run_validations()

    # Check for any critical validation errors before deserializing to user object
    if uv.errors['critical']:
        model_errors = process_model_errors(uv.errors)
        return generate_error_response(errors=model_errors, code=400)

    user, errors = uv.make_object()

    if user:
        db.session.add(user)
        db.session.commit()
        model_errors = process_model_errors(uv.errors)
        response = jsonify({'user': user.dump(), 'errors': model_errors})
        response.headers['Location'] = url_for('api_v1.get_user', userid=user.id)
        response.status_code = 200
        return response

    else:
        model_errors = process_model_errors(uv.errors)
        response = jsonify({'User': None, 'errors': model_errors})
        response.status_code = 400
        return response


@api.route('/User/<int:userid>', methods=['DELETE'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def delete_user(userid):
    """
    Delete an existing user
    """
    user = User.query.get(userid)
    if not user:
        return not_found(message='The user that was attempted to be deleted could not be found.')
    if not user.is_accessible(requesting_user=g.current_user, other_permissions=[app_permission_userdelete]):
        return forbidden(message="You do not have permission to delete user with id {}".format(user.id))
    user_id = user.id
    db.session.delete(user)
    db.session.commit()
    json_response = jsonify({'User': user_id, 'errors': []})
    return json_response, 200


def invalid_version_number(version_number, object):
    return bad_request(message='The version number supplied ({}) was invalid.  '
                               'Please supply a user version between 1 and {}'.format(version_number,
                                                                                      len(object.versions.all())))


@api.route('/User/<int:userid>/version/<int:version_number>', methods=['GET'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def get_user_version(userid, version_number):
    user = User.query.get_or_404(userid)
    if not user.is_accessible(requesting_user=g.current_user):
        return forbidden(message="You do not have permission to view user with id {}".format(user.id))

    # Handle version numbers less than 1 with an error not found w/ custom error dict
    if version_number < 1:
        return invalid_version_number(version_number=version_number, object=user)

    # Check if positive version number exists
    try:
        uv = user.versions[version_number - 1]
    except IndexError:
        return invalid_version_number(version_number=version_number, object=user)

    # Dump data using Marshmallow shcema
    schema = UserVersionSchema()
    data, _ = schema.dump(uv)
    self_url = url_for('api_v1.get_user_version', userid=user.id, version_number=version_number, _external=True)

    # Add data not easily accessible from Marshmallow schema
    data['version_number'] = version_number
    data['self_url'] = self_url

    # Define data for meta dictionary
    first_url = url_for('api_v1.get_user_version', userid=user.id, version_number=1, _external=True)
    last_url = url_for('api_v1.get_user_version', userid=user.id, version_number=len(user.versions.all()),
                       _external=True)

    if uv.next:
        next_url = url_for('api_v1.get_user_version', userid=user.id, version_number=version_number + 1, _external=True)
    else:
        next_url = None

    if uv.previous:
        previous_url = url_for('api_v1.get_user_version', userid=user.id, version_number=version_number - 1,
                               _external=True)
    else:
        previous_url = None

    meta = {'previous_url': previous_url, 'next_url': next_url, 'first_url': first_url, 'last_url': last_url}

    # Build response
    response = jsonify({'UserVersion': data, 'meta': meta, 'errors': []})
    response.headers['Location'] = self_url
    response.status_code = 200
    return response
