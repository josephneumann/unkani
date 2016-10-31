from flask import render_template
from . import main



@main.route('/', methods=['GET'])
def landing():
    return render_template('public/landing.html')

