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


def search_support_is_valid(support):
    """
    Validation function for fhir search support dictionary
    :param support:
        Valid dictionary of search support values
    :return:
        False if invalid
        True if valid
    """
    if not support or not isinstance(support, dict):
        return False
    for key in support:
        if not set(support[key].keys()) == {'ordered', 'modifier', 'prefix', 'model', 'column'}:
            return False
        if not isinstance(support[key]['ordered'], bool):
            return False
        if not support[key].get('model') or not support[key].get('column'):
            return False
        modifier_list = support[key].get('modifier')
        if not isinstance(modifier_list, list):
            return False
        for m in modifier_list:
            if m not in fhir_modifiers.keys():
                return False
        prefix_list = support[key].get('prefix')
        if not isinstance(prefix_list, list):
            return False
        for p in prefix_list:
            if p not in fhir_prefixes.keys():
                return False
    return True


def parse_fhir_search(args, base, model_support={}):
    default_support = {'_id': {'ordered': False,
                               'modifier': ['exact', 'not'],
                               'prefix': [],
                               'model': base,
                               'column': 'id'},
                       '_lastUpdated': {'ordered': True,
                                        'modifier': [],
                                        'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                        'model': base,
                                        'column': 'updated_at'}
                       }
    # TODO:  Validate input for model_support and base_model
    # Build one search support dictionary
    if model_support and not search_support_is_valid(support=model_support):
        raise ValueError('Invalid model search support')
    support = {**default_support, **model_support}

    fhir_search_spec = {}
    for arg in args:
        arg_split = arg.split(':')
        op = '__eq__'
        if arg_split[0] in support.keys():
            search_key = arg_split[0]
            try:
                search_modifier = arg_split[1].lower().strip()
                if search_modifier in support[search_key].get('modifier'):
                    op = fhir_modifiers.get(search_modifier)
            except IndexError:
                pass

            value = request.args.get(arg)
            if support[search_key].get('ordered'):
                try:
                    value_prefix = value[0:2].lower().strip()
                    if value_prefix in fhir_prefixes.keys():
                        value = value[2:]
                        op = fhir_prefixes.get(value_prefix)
                except IndexError:
                    pass
            fhir_search_spec[search_key] = {'op': op,
                                            'value': value,
                                            'model': support[search_key].get('model'),
                                            'column': support[search_key].get('column')}

    return fhir_search_spec


def fhir_apply_search_to_query(fhir_search_spec, query):
    for key in fhir_search_spec.keys():
        column = getattr(fhir_search_spec[key]['model'], fhir_search_spec[key]['column'])
        op = fhir_search_spec[key]['op']
        value = fhir_search_spec[key]['value']
        query = query.filter(getattr(column, op)(value))
    return query


def fhir_search(args, model_support, base, query):
    fhir_search_spec = parse_fhir_search(args=args, model_support=model_support, base=base)
    return fhir_apply_search_to_query(fhir_search_spec=fhir_search_spec, query=query)
