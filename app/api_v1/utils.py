from flask import request, abort, jsonify, make_response
import functools
import hashlib
from app.utils.general import url_for
from app.api_v1.errors import not_found, precondition_failed, not_modified

filter_ops = {'eq': '__eq__',  # equal
              'ne': '__ne__',  # not equal
              'lt': '__lt__',  # less than
              'le': '__le__',  # less than or equal to
              'gt': '__gt__',  # greater than
              'ge': '__ge__',  # great than or equal to
              'in': 'in_',  # in
              'like': 'like',  # like (case-sensitive)
              'ilike': 'ilike'}  # ilike (case-insensitive)


def paginate_query(query, name, max_per_page=50, error_list=[], **kwargs):
    if name is None:
        name = 'resource'

    sort = request.args.get('sort')
    filter = request.args.get('filter')
    collapse = request.args.get('collapse')

    # Look to request args for the 'page' param.  If not set default to 1.
    # 'page=1'
    page = request.args.get('page', 1, type=int)

    # Get 'per_page' param value from request args.  Make sure it is less that maximum per page set
    # 'per_page=10'
    per_page = min(request.args.get('per_page', max_per_page,
                                    type=int), max_per_page)
    # Get the boolean value for collapse
    # 'collapse=1'
    collapse = request.args.get('collapse')

    # Return pagination object
    p = query.paginate(page, per_page)

    if not p.items:
        return not_found(message='No resources could be found matching your request paramaters')

    # Set pages dict to be supplied to metadata
    pages = {'page': page, 'per_page': per_page,
             'total': p.total, 'pages': p.pages}

    # If pagination object has a previous page, set prev_url
    if p.has_prev:
        pages['prev_url'] = url_for(request.endpoint,
                                    filter=filter,
                                    sort=sort,
                                    page=p.prev_num,
                                    per_page=per_page,
                                    collapse=collapse,
                                    _external=True,
                                    **kwargs)
    else:
        pages['prev_url'] = None

    # If pagination object has next page, set next_url
    if p.has_next:
        pages['next_url'] = url_for(request.endpoint,
                                    filter=filter,
                                    sort=sort,
                                    page=p.next_num,
                                    per_page=per_page,
                                    collapse=collapse,
                                    _external=True,
                                    **kwargs)
    else:
        pages['next_url'] = None

    # Define first and last urls for pagination object
    pages['first_url'] = url_for(request.endpoint,
                                 filter=filter,
                                 sort=sort,
                                 page=1,
                                 per_page=per_page,
                                 collapse=collapse,
                                 _external=True,
                                 **kwargs)
    pages['last_url'] = url_for(request.endpoint,
                                filter=filter,
                                sort=sort,
                                page=p.pages,
                                per_page=per_page,
                                collapse=collapse,
                                _external=True, **kwargs)
    # If collapse arg is passed, only provide resource URL
    if collapse:
        items = [item.get_url() for item in p.items]
    # Otherwise return expanded resource representation, generated from
    # model.dump() method
    else:
        items = [item.dump() for item in p.items]

    response = jsonify({name: items, 'meta': pages, 'errors': error_list})
    response.status_code = 200
    return response


def register_arg_error(arg=None, type='invalid argument'):
    error = {'type': type,
             'level': 'warning',
             'message': 'invalid argument was ignored : {}'.format(arg)}
    return error


def etag(f):
    """This decorator adds an ETag header to the response."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        # only for HEAD and GET requests
        assert request.method in ['HEAD', 'GET'], \
            '@etag is only supported for GET requests'
        rv = f(*args, **kwargs)
        rv = make_response(rv)
        etag = '"' + hashlib.md5(rv.get_data()).hexdigest() + '"'
        rv.headers['Cache-Control'] = 'max-age=86400'
        rv.headers['ETag'] = etag
        if_match = request.headers.get('If-Match')
        if_none_match = request.headers.get('If-None-Match')
        if if_match:
            etag_list = [tag.strip() for tag in if_match.split(',')]
            if etag not in etag_list and '*' not in etag_list:
                rv = precondition_failed()
        elif if_none_match:
            etag_list = [tag.strip() for tag in if_none_match.split(',')]
            if etag in etag_list or '*' in etag_list:
                rv = not_modified()
        return rv

    return wrapped
