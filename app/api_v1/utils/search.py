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