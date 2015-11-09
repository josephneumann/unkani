# Application blueprint constructor
# Blueprint for application hosted in its own module
# Note: blueprint is registered with app inside create_app() factory
from flask import Blueprint

main = Blueprint('main', __name__)

#Import routes and error handlers to associate with blueprint
#Must remain at bottom to avoid circular dependencies
from . import views, errors