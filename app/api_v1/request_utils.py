import functools
from flask import request, jsonify
from app.api_v1.operation_outcome_utils import create_operation_outcome

fhir_mime_types = {
    'json': ['application/fhir+json', 'application/json+fhir', 'application/json', 'json'],
    'xml': ['application/fhir+xml', 'application/json+xml', 'application/xml', 'text/xml', 'xml'],
    'rdf': ['text/turtle', 'ttl']
}


def enforce_fhir_mimetype_charset(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):

        outcome_list = []

        # For charset prioritize accept-charset header
        accept_charset_header = request.headers.get(key='accept-charset')
        if accept_charset_header:
            if str(accept_charset_header).lower().strip() != 'utf-8':
                outcome_list.append({'severity': 'error', 'type': 'structure', 'location': ['http.accept-charset'],
                                     'details':
                                         'An invalid charset was requested in the Accept-Charset header {}'.format(
                                             accept_charset_header)})

        # For mime_type prioritize _format arg
        format_header = request.args.get(key='_format', type=str)
        if format_header:
            if str(format_header).lower().strip() not in fhir_mime_types['json']:
                outcome_list.append({'severity': 'error', 'type': 'structure', 'location': ['http._format'],
                                     'details':
                                         'An invalid mime-type was requested in the _format parameter {}'.format(
                                             format_header)})

        # Check values in the accept header to get mime type if _format was not set or charset as a param
        # of the accept header if the accept-charset header was not set
        accept_header = request.headers.get(key='accept', type=str)
        if accept_header:
            accept_header_parts = str(accept_header).split(';')
            accept_string = accept_header_parts[0]
            if accept_string:
                if str(accept_string).lower().strip() not in fhir_mime_types['json']:
                    outcome_list.append({'severity': 'error', 'type': 'structure', 'location': ['http.accept'],
                                         'details':
                                             'An invalid mime-type was requested in the Accept header: {}.'.format(
                                                 accept_string)})
                try:
                    if str(accept_header_parts[1]).lower().strip() != 'utf-8':
                        outcome_list.append(
                            {'severity': 'error', 'type': 'structure', 'location': ['http.accept'],
                             'details':
                                 'An invalid charset was requested in the Accept header charset parameter {}'.format(
                                     accept_header_parts[1])})
                except IndexError:
                    pass

        # Check content-type header for mime type and charset
        content_type_header = request.headers.get(key='content-type', type=str)
        if content_type_header:
            content_type_header_parts = str(content_type_header).split(';')
            content_string = content_type_header_parts[0]
            if content_string:
                if str(content_string).lower().strip() not in fhir_mime_types['json']:
                    outcome_list.append(
                        {'severity': 'error', 'type': 'structure', 'location': ['http.content-type'],
                         'details': 'An invalid mime-type was designated in the Content-Type header: {}'.format(
                             content_string)})
            try:
                if str(content_type_header_parts[1]).lower().strip() != 'utf-8':
                    outcome_list.append(
                        {'severity': 'error', 'type': 'structure', 'location': ['http.content-type'],
                         'details': 'An invalid charset was designated in the Content-Type header: {}'.format(
                             content_type_header_parts[1])})
            except IndexError:
                pass

        if outcome_list:
            oo = create_operation_outcome(outcome_list)
            response = jsonify(oo.as_json())
            response.status_code = 415
            response.headers['Content-Type'] = 'application/fhir+json'
            response.headers['Charset'] = 'UTF-8'
            return response

        return f(*args, **kwargs)

    return wrapped
