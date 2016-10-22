from flask import render_template, session, redirect, url_for, current_app, request

from .. import db
from ..models import User
from ..email import send_email
from . import main


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')
