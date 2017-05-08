from flask import render_template, g
from flask_login import current_user
from . import main
from app.security import return_template_context_permissions, create_user_permission


@main.context_processor
def main_context_processor():
    app_permission_dict = return_template_context_permissions()
    return app_permission_dict


@main.route('/', methods=['GET'])
def landing():
    return render_template('public/index.html')
