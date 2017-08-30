from flask import jsonify

from app.api_v1 import api


def process_model_errors(errors=None):
    if not isinstance(errors, dict):
        raise ValueError('input must be a dict with keys critical and warning')
    error_list = []
    if errors['critical']:
        for key in errors['critical']:
            level = 'critical'
            type = key
            message = dict(errors['critical']).get(key)
            error_dict = dict(level=level, type=type, message=message)
            error_list.append(error_dict)
    if errors['warning']:
        for key in errors['warning']:
            level = 'warning'
            type = key
            message = dict(errors['warning']).get(key)
            error_dict = dict(level=level, type=type, message=message)
            error_list.append(error_dict)
    return error_list


def unpack_error_dict(error_dict, code=None):
    if not isinstance(error_dict, dict):
        raise TypeError
    else:
        message = error_dict.get('message', None)
        if not message:
            raise ValueError('message must be populated for each error')
        error_type = error_dict.get('type', None)
        if not error_type:
            if isinstance(code, int):
                if code == 400:
                    error_type = 'bad request'
                elif code == 304:
                    error_type = 'not modified'
                elif code == 401:
                    error_type = 'not authorized'
                elif code == 403:
                    error_type = 'forbidden'
                elif code == 404:
                    error_type = 'not found'
                elif code == 405:
                    error_type = 'method not allowed'
                elif code == 412:
                    error_type = 'precondition failed'
                elif code == 500:
                    error_type = 'internal server error'
            else:
                error_type = 'error'
        level = error_dict.get('level', 'warning')
        if level not in ['warning', 'critical']:
            raise ValueError('level for error must be either critical or warning')

        return dict(type=error_type, level=level, message=message)


def generate_error_content(errors=None, code=None):
    error_list = []
    if not errors:
        return None
    elif isinstance(errors, list):
        for error_dict in errors:
            error_dict = unpack_error_dict(error_dict=error_dict, code=code)
            error_list.append(error_dict)
        return error_list
    elif isinstance(errors, dict):
        error_dict = unpack_error_dict(error_dict=errors, code=code)
        error_list.append(error_dict)
        return error_list


def generate_error_response(errors=None, code=None):
    if not (isinstance(errors, list) or isinstance(errors, dict)):
        raise ValueError('error input must be a list of dicts or a dict')
    else:
        error_list = generate_error_content(errors=errors, code=code)
        error_template = {"errors": error_list}
        response = jsonify(error_template)
        if code in (304, 400, 401, 403, 404, 405, 412, 500):
            response.status_code = int(code)
        return response


def not_modified(message='The resource was not modified.',
                 type='not modified', level='warning'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=304)
    return response


@api.errorhandler(400)
def bad_request(message='The request is invalid or inconsistent.', type='bad request', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=400)
    return response


@api.errorhandler(401)
def unauthorized(message='The request does not include authentication information.', type='not authorized',
                 level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=401)
    return response


@api.errorhandler(403)
def forbidden(message='The authentication credentials sent with the request are insufficient for the request.',
              type='forbidden', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=403)
    return response


@api.errorhandler(404)
def not_found(message='The resource requested was not found.', type='not found', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=404)
    return response


@api.errorhandler(405)
def method_not_allowed(message='The attempted method is not allowed.', type='method not allowed', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=405)
    return response

def precondition_failed(message='Precondition failed.', type='precondition failed', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=412)
    return response

def too_many_requests(message='You have exceeded your allowed request rate', type='too many requests', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=429)
    return response


@api.errorhandler(500)
def internal_server_error(message='An unexpected error has occurred while processing the request.',
                          type='internal server error', level='critical'):
    error_dict = {'message': message, 'type': type, 'level': level}
    response = generate_error_response(errors=error_dict, code=500)
    return response


class ValidationError(ValueError):
    pass


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(type='validation error', message=e.args[0])


class AuthenticationError(ValueError):
    pass


@api.errorhandler(AuthenticationError)
def validation_error(e):
    return bad_request(type='authentication error', message=e.args[0])
