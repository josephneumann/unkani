from flask import render_template, g
from raven.base import Raven

from . import main
from .. import sentry


# Application wide error handlers use main.app_errorhandler

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html',
                           event_id=g.sentry_event_id,
                           public_dsn=sentry.client.get_public_dsn('https'),
                           Raven=Raven
                           ), 500
