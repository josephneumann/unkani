from fhirclient.models.bundle import Bundle, BundleEntry, BundleEntrySearch, BundleLink
from fhirclient.models.fhirabstractbase import FHIRAbstractBase
from flask import request, jsonify, url_for


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
                 'ge': '__ge__'  # great than or equal to
                 # 'sa': '__gt__',  # starts after
                 # 'eb': '__lt__',  # ends before
                 # 'in': 'in_',  # in
                 # 'like': 'like',  # like (case-sensitive)
                 # 'ilike': 'ilike'
                 }  # ilike (case-insensitive)

fhir_modifiers = {'text': '',
                  'in': 'in',
                  'below': '__lt__',
                  'above': '__gt__',
                  'not-in': '',
                  'exact': '__eq__',
                  'not': '__ne__'}


def parse_fhir_search(args):
    fhir_search_spec = {}
    for arg in args:
        if arg not in ['page', '_count']:
            arg_split = arg.split(':')
            search_key = arg_split[0]
            try:
                search_modifer = arg_split[1].lower().strip()
                if search_modifer not in fhir_modifiers:
                    search_modifer = None
            except IndexError:
                search_modifer = None

            value = request.args.get(arg)
            value_prefix = None
            if search_key in ['_lastUpdated', 'birthdate', 'death-date']:
                try:
                    value_prefix = value[0:2].lower().strip()
                    if value_prefix in fhir_prefixes.keys():
                        value = value[2:]
                    else:
                        value_prefix = None
                except IndexError:
                    pass
            fhir_search_spec[search_key] = {'modifier': search_modifer,
                                            'prefix': value_prefix,
                                            'value': value}
    return fhir_search_spec