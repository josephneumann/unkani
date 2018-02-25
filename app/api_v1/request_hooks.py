from app.api_v1 import api_bp


@api_bp.before_request
def before_request():  # pragma: no cover
    pass


@api_bp.after_request
def apply_default_response_headers(response):
    response.headers['Content-Type'] = 'application/fhir+json'
    response.headers['Charset'] = 'UTF-8'
    return response
