from flask import render_template, g, request, jsonify, current_app
from raven.base import Raven

from . import main
from .. import sentry


# Application wide error handlers use main.app_errorhandler
@main.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'resource not found',
                            'message': 'The resource you requested could not be found'})
        response.status_code = 404
        return response
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response

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
