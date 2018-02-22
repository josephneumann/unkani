from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntrySearch, BundleLink
from fhirclient.models.fhirabstractbase import FHIRAbstractBase
from fhirclient.models.operationoutcome import OperationOutcome, OperationOutcomeIssue
from fhirclient.models.narrative import Narrative
from fhirclient.models.codeableconcept import CodeableConcept
from flask import request, jsonify, url_for, render_template
import functools
from app.models.fhir.codesets import ValueSet

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


def paginate_query(query):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('_count', 10, type=int)
    return query.paginate(page=page, per_page=per_page), per_page


def set_bundle_page_links(bundle, pagination, per_page):
    addtnl_args = request.args.to_dict(flat=False)
    for x in ['page', '_count']:
        try:
            del addtnl_args[x]
        except KeyError:
            pass
    link_self = BundleLink()
    link_self.relation = 'self'
    if not pagination.has_prev:
        page = 1
    else:
        page = pagination.next_num - 1
    link_self.url = url_for(request.endpoint, page=page, _count=per_page, _external=True, **addtnl_args)

    link_first = BundleLink()
    link_first.relation = 'first'
    link_first.url = url_for(request.endpoint, page=1, _count=per_page, _external=True, **addtnl_args)

    link_last = BundleLink()
    link_last.relation = 'last'
    link_last.url = url_for(request.endpoint, page=pagination.pages, _count=per_page, _external=True, **addtnl_args)

    bundle.link = [link_self, link_first, link_last]

    if pagination.has_prev:
        link_prev = BundleLink()
        link_prev.relation = 'previous'
        link_prev.url = url_for(request.endpoint, page=pagination.prev_num, _count=per_page, _external=True,
                                **addtnl_args)
        bundle.link.append(link_prev)

    if pagination.has_next:
        link_next = BundleLink()
        link_next.relation = 'next'
        link_next.url = url_for(request.endpoint, page=pagination.next_num, _count=per_page, _external=True,
                                **addtnl_args)
        bundle.link.append(link_next)

    return bundle


def create_bundle_search_entry(obj):
    try:
        fhir_obj = obj.fhir
        if not isinstance(fhir_obj, FHIRAbstractBase):
            raise TypeError

        e = BundleEntry()
        e.fullUrl = getattr(fhir_obj, 'id')
        e.resource = fhir_obj
        e.search = BundleEntrySearch()
        e.search.mode = 'match'
        # TODO: Allow modified certainty code of 0 to 1
        e.search.score = 1
        return e

    except AttributeError or TypeError:
        raise TypeError('Object did not have an attribute FHIR that generates an FHIR object')


def create_bundle(query, paginate=True):
    # Initialize searchset bundle
    b = Bundle()
    b.type = 'searchset'

    # Handle _summary arg
    # TODO: Refactor into separate function or decorator
    summary = request.args.get('_summary')
    if summary:
        if summary == 'count':
            b.total = len(query.all())
            return b
    # TODO: Handle summary = True and summary = Text and summary = Data
    # Apply pagination if desired and set links
    if paginate:
        p, per_page = paginate_query(query=query)
        b = set_bundle_page_links(bundle=b, pagination=p, per_page=per_page)
        records = p.items
        b.total = p.total
    # Otherwise, execute query as-is
    else:
        records = query.all()
        b.total = len(records)

    # Loop through results to generate bundle entries
    for r in records:
        try:
            # Try creating a search entry for the bundle
            e = create_bundle_search_entry(obj=r)
            # If entry can be made (e.g. if object has working fhir attribute) append to bundle
            try:
                b.entry.append(e)
            except AttributeError:
                b.entry = [e]
        # Silently ignore items returned in the query that can't be turned into bundle entries
        except TypeError:
            # TODO: Improve error handling or feedback on this function for items that fail to be created
            pass

    # TODO: Add OperationOutcome to bundle attribute
    return b


fhir_prefixes = {'eq': '__eq__',  # equal
                 'ne': '__ne__',  # not equal
                 'lt': '__lt__',  # less than
                 'le': '__le__',  # less than or equal to
                 'gt': '__gt__',  # greater than
                 'ge': '__ge__',  # great than or equal to
                 'in': 'in_'  # in
                 # 'ni': 'notin_'  # not in
                 # 'sa': '__gt__',  # starts after
                 # 'eb': '__lt__',  # ends before
                 # 'like': 'like',  # like (case-sensitive)
                 # 'ilike': 'ilike'
                 }  # ilike (case-insensitive)

fhir_modifiers = {'contains': 'ilike',
                  'in': 'in_',
                  'below': '__lt__',
                  'above': '__gt__',
                  'not-in': 'notin_',
                  'exact': '__eq__',
                  'not': '__ne__'}  # TODO: Handle :missing, :text


def parse_fhir_search(args):
    fhir_search_spec = {}
    for arg in args:
        if arg not in ['page', '_count']:
            arg_split = arg.split(':')
            search_key = arg_split[0]
            search_modifer = None
            search_modifer_op = None
            try:
                n_search_modifer = arg_split[1].lower().strip()
                if n_search_modifer in fhir_modifiers:
                    search_modifer = n_search_modifer
                    search_modifer_op = fhir_modifiers.get(n_search_modifer)
            except IndexError:
                pass

            value = request.args.get(arg)
            value_prefix = None
            if search_key in ['_lastUpdated']:  # Add 'birthdate', 'death-date' for patient
                try:
                    value_prefix = value[0:2].lower().strip()
                    if value_prefix in fhir_prefixes.keys():
                        value = value[2:]
                    else:
                        value_prefix = None
                except IndexError:
                    pass
            fhir_search_spec[search_key] = {'modifier': search_modifer,
                                            'modifierOp': search_modifer_op,
                                            'prefix': value_prefix,
                                            'value': value}
    return fhir_search_spec


def create_operation_outcome(outcome_list):
    """
    Helper function to construct and OperationOutcome object from the appropriate data structure

    :param outcome_list:
    An array of dicts containing the keys necessary to generate an OperationOutcome FHIR STU 3.0 object

        outcome_list = [{'severity': None, 'type': None, 'location': [], 'diagnostics': None, 'expression': None,
                'details': None}]
        # Severity and Type are REQUIRED

    :return:
    A FHIR-Client OperationOutcome Object
    """
    oo = OperationOutcome()

    narrative = Narrative()
    narrative.status = 'additional'
    narrative.div = render_template('fhir/operation_outcome.html', outcome_list=outcome_list)
    oo.text = narrative

    severity_codes = ValueSet.query.filter(ValueSet.resource_id == 'issue-severity').first().code_set
    type_codes = ValueSet.query.filter(ValueSet.resource_id == 'issue-type').first().code_set

    for x in outcome_list:
        issue_severity = None
        issue_type = None
        issue_location = []
        issue_diagnostics = None
        issue_expression = None
        issue_details = None
        if 'severity' in x.keys():
            issue_severity = x.get('severity').lower().strip()
            if issue_severity not in severity_codes:
                issue_severity = None

        if 'type' in x.keys():
            issue_type = x.get('type').lower().strip()
            if issue_type not in type_codes:
                issue_type = None

        if 'details' in x.keys():
            details = x.get('details')
            if details:
                details_cc = CodeableConcept()
                details_cc.text = details
                issue_details = details_cc
            pass

        if 'diagnostics' in x.keys():
            diagnostics = x.get('diagnostics')
            if diagnostics:
                issue_diagnostics = diagnostics

        if 'location' in x.keys():
            location = x.get('location')
            if location:
                if isinstance(location, list):
                    for i in location:
                        issue_location.append(i)
                elif isinstance(location, str):
                    issue_location.append(location)

        if 'expression' in x.keys():
            expression = x.get('expression')
            if expression:
                issue_expression = expression

        issue = OperationOutcomeIssue()
        if issue_severity:
            issue.severity = issue_severity
        if issue_type:
            issue.code = issue_type
        if issue_location:
            issue.location = issue_location
        if issue_diagnostics:
            issue.diagnostics = issue_diagnostics
        if issue_expression:
            issue.expression = issue_expression
        if issue_details:
            issue.details = issue_details

        try:
            oo.issue.append(issue)
        except AttributeError:
            oo.issue = [issue]

    return oo


def create_token_expired_operation_outcome(e):
    oo = create_operation_outcome(outcome_list=[
        {'severity': 'error', 'type': 'expired', 'location': [url_for('api_v1.new_token', _external=True)],
         'diagnostics': e.args[0], 'details': 'Authentication token expired: complete authentication for new token'}])
    return oo
