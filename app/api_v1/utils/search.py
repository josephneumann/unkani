from flask import request

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


def parse_fhir_search(args, model_support={}):
    default_support = {'_id': {'ordered': False,
                               'modifier': ['exact', 'not'],
                               'prefix': []},
                       '_lastUpdated': {'ordered': True,
                                        'modifier': [],
                                        'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne']}
                       }
    #TODO:  Validate input for model_support and base_model
    # Build one search support dictionary
    support = {**default_support, **model_support}

    fhir_search_spec = {}
    for arg in args:
        arg_split = arg.split(':')
        search_key, search_modifier = None, None
        op = '__eq__'
        if arg_split[0] in support.keys():
            search_key = arg_split[0]
            try:
                n_search_modifier = arg_split[1].lower().strip()
                if n_search_modifier in support[search_key].get('modifier'):
                    search_modifier = n_search_modifier
                    op = fhir_modifiers.get(n_search_modifier)
            except IndexError:
                pass

            value = request.args.get(arg)
            value_prefix = None
            if support[search_key].get('ordered'):
                try:
                    n_value_prefix = value[0:2].lower().strip()
                    if n_value_prefix in fhir_prefixes.keys():
                        value = value[2:]
                        op = fhir_prefixes.get(n_value_prefix)
                        value_prefix = n_value_prefix
                except IndexError:
                    pass
            fhir_search_spec[search_key] = {'modifier': search_modifier,
                                            'op': op,
                                            'prefix': value_prefix,
                                            'value': value}
    return fhir_search_spec
