from flask import render_template, g, request, jsonify, current_app
from raven.base import Raven

from . import main
from .. import sentry


#################################
# JSON ERROR GENERATION UTILS
#################################
# TODO: Refactor errors to be DRY and resolve import errors from API blueprint

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


# Application wide error handlers use main.app_errorhandler
@main.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def not_found(e):
    if not request.accept_mimetypes.accept_html and request.accept_mimetypes.accept_json:
        error_dict = {'message': 'Resource not found', 'type': 'not found', 'level': 'critical'}
        response = generate_error_response(errors=error_dict, code=404)
        return response
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if not request.accept_mimetypes.accept_html and request.accept_mimetypes.accept_json:
        error_dict = {'message': 'Internal server error', 'type': 'internal server error',
                      'level': 'critical'}
        response = generate_error_response(errors=error_dict, code=500)
        return response
    else:
        if not current_app.config['SENTRY_DISABLE']:
            return render_template('errors/500.html',
                                   event_id=g.sentry_event_id,
                                   public_dsn=sentry.client.get_public_dsn('https'),
                                   Raven=Raven
                                   ), 500
        else:
            return render_template('errors/500.html'), 500


class ValidationError(ValueError):
    pass
