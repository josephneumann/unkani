from flask import jsonify
from app.api_v1 import api_bp


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
