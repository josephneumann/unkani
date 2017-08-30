from flask import request, jsonify, g, url_for
from sqlalchemy import or_, and_
from sqlalchemy.orm import aliased
import json

from app import sa
from app.security import *
from . import api
from .authentication import token_auth
from .phone_numbers import PhoneNumberAPI
from .addresses import AddressAPI
from .email_addresses import EmailAddressAPI, EmailAddress
from .utils import paginate_query, filter_ops, register_arg_error, etag
from .errors import *
from .rate_limit import rate_limit
from app.models.user import User, lookup_user_by_email, lookup_user_by_username, unkani_password_hasher
from app.models.role import Role
from app.models.address import Address
from app.models.phone_number import PhoneNumber
from app.models.app_group import AppGroup
from app.utils.demographics import *
from app.flask_sendgrid import send_email


@api.route('/users', methods=['GET'])
@token_auth.login_required
@app_permission_userprofileupdate.require(http_exception=403)
@rate_limit(limit=5, period=15)
@etag
def get_users():
    #TODO: Add filtering by app group info

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
    query = User.query\
        .join(Role)\
        .filter(or_(Role.level < level, User.id == id))\
        .join(EmailAddress)\
        .filter(and_(EmailAddress.primary == True, EmailAddress.active == True))\
        .filter(sa.session.query(ua) \
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
                    query = query.join(Address).filter(Address.primary==True).filter(Address.active==True)
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

    response = paginate_query(query=query, name='users', error_list=error_list, max_per_page=50)
    return response


@api.route('/users/<int:userid>', methods=['GET'])
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
        response = jsonify({'user': data, 'errors': []})
        response.headers['Location'] = url_for('api_v1.get_user', userid=user.id)
        response.status_code = 200
        return response


@api.route('/users', methods=['POST'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def new_user():
    #TODO: Default app group to that of requesting user when creating.  Might need to set a default on assoc. table.
    """
    Register a new user
    """
    if not app_permission_usercreate.can():
        return forbidden(message='You do not have sufficient permissions to crete a new user.')
    json_data = request.get_json()
    uv = UserAPI()
    uv.loads_json(json_data)
    uv.run_validations()
    if not uv.errors['critical'].get('email'):
        if lookup_user_by_email(uv.email.email):
            uv.errors['critical']['email'] = 'The email {} is already registered.'.format(uv.email)
    if not uv.errors['critical'].get('username'):
        if lookup_user_by_username(uv.username):
            uv.errors['critical']['username'] = 'The username {} is already registered.'.format(uv.username)
    uv.run_permission_checks()
    user, errors = uv.make_object()
    if uv.errors['critical']:
        model_errors = process_model_errors(uv.errors)
        return generate_error_response(errors=model_errors, code=400)
    elif isinstance(user, User):
        sa.session.add(user)
        sa.session.commit()
        model_errors = process_model_errors(uv.errors)
        data = {"user": user.dump(), "errors": model_errors}
        response = jsonify(data)
        response.headers['Location'] = url_for('api_v1.get_user', userid=user.id)
        response.status_code = 201
        return response
    else:
        response = jsonify({"user": None, "errors": {'critical': {'user creation': 'failed to create user'}}})
        response.status_code = 400
        return response


@api.route('/users/<int:userid>', methods=['PUT', 'PATCH'])
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

    # Check email and username for changes and overlap with other users
    if not uv.errors['critical'].get('email'):
        if uv.email and uv.email != uv.user.email.email:
            email_match = lookup_user_by_email(uv.email.email)
            if email_match and email_match != uv.user:
                uv.errors['critical']['email'] = 'The email {} is already registered.'.format(uv.email)

    if not uv.errors['critical'].get('username'):
        if uv.username and uv.username != uv.user.username:
            username_match = lookup_user_by_username(uv.username)
            if username_match and username_match != uv.user:
                uv.errors['critical']['username'] = 'The username {} is already registered.'.format(uv.username)

    # Check for any critical validation errors before deserializing to user object
    if uv.errors['critical']:
        model_errors = process_model_errors(uv.errors)
        return generate_error_response(errors=model_errors, code=400)

    user, errors = uv.make_object()

    if user:
        sa.session.add(user)
        sa.session.commit()
        model_errors = process_model_errors(uv.errors)
        response = jsonify({'user': user.dump(), 'errors': model_errors})
        response.headers['Location'] = url_for('api_v1.get_user', userid=user.id)
        response.status_code = 200
        return response

    else:
        model_errors = process_model_errors(uv.errors)
        response = jsonify({'user': None, 'errors': model_errors})
        response.status_code = 400
        return response


@api.route('/users/<int:userid>', methods=['DELETE'])
@token_auth.login_required
@rate_limit(limit=5, period=15)
def delete_user(userid):
    """
    Delete an existing user
    """
    user = User.query.get(userid)
    if not user:
        return not_found(message='The user that was attempted to be deleted could not be found.')
    if not g.current_user.is_accessible(requesting_user=user, other_permissions=[app_permission_userdelete]):
        return forbidden(message="You do not have permission to delete user with id {}".format(user.id))
    user_id = user.id
    sa.session.delete(user)
    sa.session.commit()
    json_response = jsonify({"user": user_id, "errors": []})
    return json_response, 200


##################################################################################################
# USER API MEDIATOR OBJECT - HANDLER FOR NORMALIZATION, VALIDATION AND DESERIALIZATION FROM JSON
##################################################################################################

class UserAPI:
    def __init__(self):
        self.errors = {"critical": {},
                       "warning": {}}
        self._user = None

        self.first_name = None
        self.last_name = None
        self.username = None
        self.dob = None
        self.sex = None
        self.email = None
        self.description = None
        self.active = None
        self.confirmed = None
        self.password = None
        self.role_id = None
        self.phone_number = None
        self.address = {}

    @property
    def user(self):
        if self._user:
            return self._user
        else:
            return None

    @user.setter
    def user(self, user):
        if user is None:
            pass
        elif isinstance(user, User):
            self._user = user
        else:
            raise TypeError('Object assigned to user was not a SQL Alchemy User type object.')

    def loads_json(self, data):

        ud = None

        if isinstance(data, dict):
            ud = data
        else:
            try:
                ud = json.loads(data)
            except:
                self.errors['critical']['json decode error'] = 'An error occurred when attempting to decode JSON.'
        if ud:
            self.first_name = ud.get('first_name', None)
            self.last_name = ud.get('last_name', None)
            self.username = ud.get('username', None)
            self.dob = ud.get('dob', None)
            self.sex = ud.get('sex', None)
            self.email = ud.get('email', None)
            self.description = ud.get('description', None)
            self.active = ud.get('active', None)
            self.confirmed = ud.get('confirmed', None)
            self.password = ud.get('password', None)
            self.role_id = ud.get('role_id', None)
            self.phone_number = ud.get('phone_number', None)

            self.address = ud.get('address', {})

    def validate_first_name(self):
        if self.first_name:
            self.first_name = normalize_name(name=self.first_name)
        else:
            self.first_name = None

    def validate_last_name(self):
        if self.last_name:
            self.last_name = normalize_name(self.last_name)

        else:
            self.last_name = None

    def validate_dob(self):
        if self.dob:
            try:
                self.dob = validate_dob(self.dob)
            except ValueError as e:
                self.errors['critical']['dob'] = e.args[0]
                self.dob = None

    def validate_sex(self):
        if self.sex:
            try:
                self.sex = validate_sex(self.sex)
            except ValueError as e:
                self.errors['warning']['sex'] = e.args[0]
                self.sex = None

    def validate_username(self):
        if isinstance(self.username, str):
            self.username = str(self.username).upper().strip()
        elif not self.user:
            self.errors['critical']['username'] = 'A username string was not provided.  A username is required.'
            self.username = None

    def validate_description(self):
        if isinstance(self.description, str):
            pass
        else:
            self.description = None

    def validate_active(self):
        if isinstance(self.active, bool):
            self.active = self.active
        else:
            self.active = None

    def validate_confirmed(self):
        # Check for boolean input of confirmed
        if isinstance(self.confirmed, bool):
            self.confirmed = self.confirmed
        else:
            self.confirmed = None

    def validate_password(self):
        if isinstance(self.password, str):
            pass
        else:
            self.password = None

    def validate_role_id(self):
        if self.role_id:
            roles = Role.query.all()
            role_ids = []
            for role in roles:
                role_ids.append(role.id)
            if self.role_id not in role_ids:
                self.role_id = None
                self.errors['warning']['role'] = 'An invalid id was passed as a role_id: {}'.format(self.role_id)

    # Validate email, set self.email to EmailAddress object if valid, None if not.  Process errors to self.errors
    def validate_email(self):
        if self.email:
            api = EmailAddressAPI(email=self.email, primary=True, active=True)
            api.run_validations()
            email_object, errors = api.make_object()

            # If email object cannot be created, process the EmailAddressAPI Errors
            if not email_object:
                self.email = None
            elif isinstance(email_object, EmailAddress):
                email_object.primary = True
                email_object.active = True
                self.email = email_object

            # Surface errors from EmailAddressAPI and log to error dict of UserAPI
            if errors['critical']:
                if not getattr(self.errors['critical'], 'email', None):
                    self.errors['critical']['email'] = {}
                for key in errors['critical']:
                    self.errors['critical']['email'][key] = errors['critical'][key]

            if errors['warning']:
                if not getattr(self.errors['warning'], 'email', None):
                    self.errors['warning']['email'] = {}
                for key in errors['warning']:
                    self.errors['warning']['email'][key] = errors['warning'][key]

        # Make sure an email was created or already existed
        if not self.email and not self.user:
            self.errors['critical']['email'][
                'missing'] = 'A valid email was not provided during user creation.  This is required.'

    # Validate phone, set self.phone_number to PhoneNumber object if valid, None if not.  Process errors to self.errors
    def validate_phone_number(self):
        if self.phone_number:
            pn = PhoneNumberAPI(number=self.phone_number, type='MOBILE', active=True, primary=True)
            pn.run_validations()
            phone_number, errors = pn.make_object()

            # If phone number object cannot be created, process the PhoneNumberAPI Errors
            if not phone_number:
                self.phone_number = None
            elif isinstance(phone_number, PhoneNumber):
                phone_number.active = True
                phone_number.primary = True
                self.phone_number = phone_number

            # Surface errors from PhoneNumberAPI and log to error dict of UserAPI
            if errors['critical']:
                if not getattr(self.errors['warning'], 'phone_number', None):
                    self.errors['warning']['phone_number'] = {}
                for key in errors['critical']:
                    self.errors['warning']['phone_number'][key] = errors['critical'][key]

            if errors['warning']:
                if not getattr(self.errors['warning'], 'phone_number', None):
                    self.errors['warning']['phone_number'] = {}
                for key in errors['warning']:
                    self.errors['warning']['phone_number'][key] = errors['warning'][key]

    def validate_address(self):
        if self.address:
            if not isinstance(self.address, dict):
                self.errors['warning']['address']['invalid_format'] = 'Address information was not supplied as' \
                                                                      ' a dictionary of key value pairs.  The address' \
                                                                      ' for the user could not be set.'
                self.address = None
            else:
                addr_dict = dict(self.address)

                address1 = addr_dict.get('address1', None)
                address2 = addr_dict.get('address2', None)
                city = addr_dict.get('city', None)
                state = addr_dict.get('state', None)
                zipcode = addr_dict.get('zipcode', None)
                primary = addr_dict.get('primary', False)
                active = addr_dict.get('active', True)

                api = AddressAPI(address1=address1, address2=address2, city=city, state=state, zipcode=zipcode,
                                 active=active, primary=primary)
                api.run_validations()
                a, errors = api.make_object()

                if not a:
                    self.errors['warning']['address'][
                        'address_creation'] = 'Unable to create an address from the supplied data.'
                    self.address = None

                if isinstance(a, Address):
                    if errors['critical'] or errors['warning']:
                        if errors['critical']:
                            for key in errors['critical']:
                                self.errors['warning']['address'][key] = errors['critical'][key]
                        if errors['warning']:
                            for key in errors['warning']:
                                self.errors['warning']['address'][key] = errors['warning'][key]

                    a.primary = True
                    a.active = True

                    self.address = a

    def permission_check_active(self):
        if isinstance(self.active, bool):
            if not app_permission_useractivation.can():
                self.active = None
                self.errors['warning']['permission: user deactivate'] = 'Could not set user activation. ' \
                                                                        'Permission denied. User must be activated or' \
                                                                        ' deactivated by an admin.'

    def permission_check_confirmed(self):
        if isinstance(self.confirmed, bool):
            # Verify permission to force set User.confirmed
            if not app_permission_userforceconfirmation.can():
                # Set to None.  Will not be written to user object during de-serialization
                self.confirmed = None
                self.errors['warning']['permission: force confirm'] = 'Attempt to force set confirmation failed.' \
                                                                      ' Permission not granted to user.'

    def permission_check_password(self):
        if self.user and self.password:
            if not app_permission_userpasswordchange.can():
                self.password = None
                self.errors['warning']['password'] = 'Insufficient permissions to update another users password.'

    def permission_check_role_id(self):
        if self.role_id:
            if not app_permission_userrolechange.can():
                self.role_id = None
                self.errors['warning']['role'] = 'Failed setting role_id for user due to insufficient permissions.'
            if Role.query.get(self.role_id).level > g.current_user.role.level:
                self.role_id = None
                self.errors['warning']['role'] = 'Could not set role to a role with a higher permission' \
                                                 ' level than the requesting user.'

    def run_validations(self):
        self.validate_first_name()
        self.validate_last_name()
        self.validate_dob()
        self.validate_sex()
        self.validate_username()
        self.validate_confirmed()  # Must run after email
        self.validate_email()
        self.validate_phone_number()
        self.validate_active()
        self.validate_description()
        self.validate_password()
        self.validate_role_id()
        self.validate_address()

    def run_permission_checks(self):
        self.permission_check_active()
        self.permission_check_confirmed()
        self.permission_check_role_id()
        self.permission_check_password()

    def make_object(self):

        if self.errors['critical']:
            return None, self.errors

        else:
            if isinstance(self.user, User):
                u = self.user
                if self.role_id:
                    u.role_id = self.role_id
            else:
                u = User(role_id=self.role_id)

            if self.first_name:
                u.first_name = self.first_name
            if self.last_name:
                u.last_name = self.last_name
            if self.dob:
                u.dob = self.dob
            if self.sex:
                u.sex = self.sex
            if self.username:
                u.username = self.username
            if isinstance(self.email, EmailAddress):
                # Set the email property of the user
                # User model handles setting switching old emails to inactive and not primary
                update_existing = False
                existing_addresses = u.email_addresses.all()
                if existing_addresses:
                    existing_primary_address = u.email
                    if self.email.email == existing_primary_address.email:
                        update_existing = True
                    else:
                        existing_primary_address.primary = False
                        existing_primary_address.active = False
                        for a in existing_addresses:
                            if a == existing_primary_address:
                                pass
                            elif self.email.email == a.email:
                                a.primary = True
                                a.active = True
                                update_existing = True
                if update_existing:
                    self.email = None

                if self.email:

                    u.email_addresses.append(self.email)

                    if not isinstance(self.confirmed, bool):
                        self.confirmed = False
                    if self.user and not self.confirmed:
                        self.errors['warning']['account_confirmation'] = 'Email address has been changed.  The' \
                                                                         ' account requires confirmation.'
                        token = u.generate_email_change_token(self.email.email.lower())
                        send_email(subject='Unkani - Email Change', to=[self.email.email.lower()],
                                   template='auth/email/change_email',
                                   token=token, user=self.user)

            if isinstance(self.phone_number, PhoneNumber):
                update_existing = False
                existing_addresses = u.phone_numbers.all()
                if existing_addresses:
                    existing_primary_address = u.phone_number
                    if self.phone_number.number == existing_primary_address.number:
                        update_existing = True
                    else:
                        existing_primary_address.primary = False
                        existing_primary_address.active = False
                        for a in existing_addresses:
                            if a == existing_primary_address:
                                pass
                            elif self.phone_number.number == a.number:
                                a.primary = True
                                a.active = True
                                update_existing = True
                if update_existing:
                    self.phone_number = None

                if self.phone_number:
                    u.phone_numbers.append(self.phone_number)

            if self.description:
                u.description = self.description

            # Set password if validation and permission passes
            if self.password:
                u.password = self.password

            # Set active is validation and permission passes
            if isinstance(self.active, bool):
                u.active = self.active

            # Set confirmation if True / False is set and permissions are in place
            if isinstance(self.confirmed, bool):
                u.confirmed = self.confirmed

            if isinstance(self.address, Address):
                update_existing = False
                existing_addresses = u.addresses.all()
                if existing_addresses:
                    existing_primary_address = u.address
                    new_address_hash = self.address.generate_address_hash()
                    if new_address_hash == existing_primary_address.address_hash:
                        update_existing = True
                    else:
                        existing_primary_address.primary = False
                        existing_primary_address.active = False
                        for a in existing_addresses:
                            if a == existing_primary_address:
                                pass
                            elif new_address_hash == a.address_hash:
                                a.primary = True
                                a.active = True
                                update_existing = True
                if update_existing:
                    self.address = None

                if self.address:
                    u.addresses.append(self.address)

            self.user = u

            return self.user, self.errors
