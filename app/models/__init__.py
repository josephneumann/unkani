from flask import _app_ctx_stack, _request_ctx_stack
from sqlalchemy.orm import configure_mappers
from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import FlaskPlugin, PropertyModTrackerPlugin


def fetch_current_user_id():
    from flask_login import current_user

    # Return None if we are outside of request context.
    if _app_ctx_stack.top is None or _request_ctx_stack.top is None:
        return
    try:
        return current_user.id
    except AttributeError:
        try:
            return g.current_user.id
        except AttributeError:
            return


make_versioned(plugins=[FlaskPlugin(current_user_id_factory=fetch_current_user_id), PropertyModTrackerPlugin()])

from .user import *
from .role import *
from .app_permission import *
from app.models.fhir.address import *
from .phone_number import *
from .email_address import *
from app.models.fhir.patient import *
from .app_group import *
from .source_data import *
from app.models.fhir import *

configure_mappers()
