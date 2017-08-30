from flask import render_template, g, request, jsonify, current_app
from raven.base import Raven

from . import main
from .. import sentry


# Application wide error handlers use main.app_errorhandler
@main.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
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
