from flask import request
import unidecode
from app.api_v1.errors.exceptions import *
from app.utils.type_validation import *

fhir_prefixes = {'eq': '__eq__',  # equal
                 'ne': '__ne__',  # not equal
                 'lt': '__lt__',  # less than
                 'le': '__le__',  # less than or equal to
                 'gt': '__gt__',  # greater than
                 'ge': '__ge__'  # greater than or equal to
                 }
fhir_modifiers = {'contains': 'ilike',
                  'in': 'in_',
                  'below': '__lt__',
                  'above': '__gt__',
                  'not-in': 'notin_',
                  'exact': '__eq__',
                  'not': '__ne__',
                  'missing': None}  # TODO: Handle :text


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
        if not set(support[key].keys()) == {'ordered', 'modifier', 'prefix', 'model', 'column', 'type', 'validation'}:
            return False
        if not isinstance(support[key]['ordered'], bool):
            return False
        if not support[key].get('model') or not support[key].get('column'):
            return False
        if not support[key].get('type') or support[key].get('type') not in ['bool', 'datetime', 'int',
                                                                            'string', 'timestamp', 'date',
                                                                            'numeric']:
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
                               'column': 'id',
                               'type': 'int',
                               'validation': []},
                       '_lastUpdated': {'ordered': True,
                                        'modifier': [],
                                        'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                        'model': base,
                                        'column': 'updated_at',
                                        'type': 'datetime',
                                        'validation': []}
                       }
    # Build one search support dictionary
    if model_support and not search_support_is_valid(support=model_support):
        raise ValueError('Invalid model search support')
    support = {**default_support, **model_support}

    fhir_search_spec = {}
    for arg in args:
        arg_split = arg.split(':')
        op = None
        if arg_split[0] in support.keys():
            input_value = request.args.get(arg)
            search_key = arg_split[0]
            value = None
            value_forced_by_operator = False
            try:
                search_modifier = arg_split[1].lower().strip()
                if search_modifier in support[search_key].get('modifier'):
                    # Handle special syntax for :missing param which checks for Null / Not Null
                    if search_modifier == 'missing':
                        # Indicate the value type is forced by the param modifier
                        value_forced_by_operator = True
                        try:
                            value = validate_bool(value=input_value, error=True)
                            if isinstance(value, bool):
                                if value:
                                    op = 'is_'
                                    value = None
                                else:
                                    op = 'isnot'
                                    value = None
                        except ValueError:
                            raise ValidationError(
                                'The value for parameter ({}) with modifier (missing) was ({}) and could not be validated as a boolean input for the search' \
                                    .format(search_key, input_value))

                    elif search_modifier == 'not' and support[search_key].get('type') == 'bool':
                        op = 'isnot'


                    # Otherwise use the operators in the lookup dictionary and the value as-is
                    else:
                        op = fhir_modifiers.get(search_modifier)
                else:
                    raise ValidationError('The search parameter ({}) does not support the modifier ({})' \
                                          .format(search_key, search_modifier))
            except IndexError:
                pass

            if support[search_key].get('ordered'):
                try:
                    value_prefix = input_value[0:2].lower().strip()
                    if value_prefix in fhir_prefixes.keys():
                        input_value = input_value[2:]
                        op = fhir_prefixes.get(value_prefix)
                except IndexError:
                    pass

            if not value_forced_by_operator:
                param_type = support[search_key].get('type')
                if param_type == 'bool':
                    try:
                        value = validate_bool(value=input_value, error=True)
                    except ValueError:
                        raise ValidationError(
                            'The value for parameter ({}) was ({}) and could not be validated as a boolean input for the search' \
                                .format(search_key, input_value))
                elif param_type in ['datetime', 'date', 'timestamp']:
                    to_date = False
                    if param_type == 'date':
                        to_date = True
                    try:
                        value = validate_datetime(value=input_value, error_out=True, to_date=to_date)
                    except DatetimeParseError:
                        raise ValidationError(
                            'The value for parameter ({}) was ({}) and could not be validated as a datetime input for the search' \
                                .format(search_key, input_value))
                if param_type == 'string': # Deal with case comparison
                    input_value = unidecode.unidecode(input_value) # Handle accents per FHIR
                    if op == 'ilike':  # Handles the :contains modifier for string parameters
                        value = '%' + str(input_value) + '%'
                    if not op:  # If no modifier is defined for string parameters a case-insensitive starts_with comp
                        op = 'ilike'
                        value = str(input_value) + '%'
                if not value:
                    value = input_value

            if not op:
                op = '__eq__'

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
