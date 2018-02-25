from flask import render_template, g, request, jsonify, current_app
from app.main import main


#################################
# JSON ERROR GENERATION UTILS
#################################
def request_wants_json():
    """
    Helper function to determine if client request prefers to receive a JSON response

    :return:
        True if request Accept header includes a valid JSON mimetype AND the JSON mimetype is preferred
        over the text/html mimetype
    """
    json_mimetypes = current_app.config['ALLOWED_MIMETYPES']['json']
    html_mimetypes = current_app.config['ALLOWED_MIMETYPES']['html']
    combined_mimetypes = json_mimetypes + html_mimetypes

    best = request.accept_mimetypes.best_match(
        combined_mimetypes,
        default='text/html')
    return best in json_mimetypes


# Application wide error handlers use main.app_errorhandler
@main.app_errorhandler(403)
def forbidden(e):
    """
    Handle 403 errors raised in the application.  Respect Accept mimetypes
    :param e:
        Exception raised
    :return:
        403 html template rendered or 403 JSON error response
    """
    if request_wants_json():
        from app.api_v1.errors.fhir_errors import fhir_error_response
        response = fhir_error_response(status_code=403, outcome_list=[
            {'severity': 'error', 'type': 'forbidden', 'diagnostics': [str(e)],
             'details': 'Forbidden - not authorized'}])
        return response
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def not_found(e):
    """
    Handle 404 errors raised in the application.  Respect Accept mimetypes
    :param e:
        Exception raised
    :return:
        403 html template rendered or 404 JSON error response
    """
    if request_wants_json():
        from app.api_v1.errors.fhir_errors import fhir_error_response
        response = fhir_error_response(status_code=404, outcome_list=[
            {'severity': 'fatal', 'type': 'not-found', 'diagnostics': [str(e)],
             'details': 'Resource not found'}])
        return response
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    """
    Handle 404 errors raised in the application.  Respect Accept mimetypes
    :param e:
        Exception raised
    :return:
        403 html template rendered or 404 JSON error response"""
    if request_wants_json():
        from app.api_v1.errors.fhir_errors import fhir_error_response
        response = fhir_error_response(status_code=500, outcome_list=[
            {'severity': 'fatal', 'type': 'exception', 'diagnostics': [str(e)],
             'details': 'Internal server error'}])
        return response
    return render_template('errors/500.html'), 500


class ValidationError(ValueError):
    # TODO: Find usages and handle appropriately
    pass
