from flask import request
import unidecode
from app.api_v1.errors.exceptions import *
from app.utils.type_validation import *
from sqlalchemy import and_, or_

# Dict of valid FHIR STU 3 ordered search value prefixes and their SQLAlchemy column operator equivalent
fhir_prefixes = {'eq': '__eq__',  # equal
                 'ne': '__ne__',  # not equal
                 'lt': '__lt__',  # less than
                 'le': '__le__',  # less than or equal to
                 'gt': '__gt__',  # greater than
                 'ge': '__ge__'  # greater than or equal to
                 }
# Dict of valid FHIR STU 3 search modifiers and their SQLAlchemy column operator equivalent
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
    # Did we get a non-empty dict?
    if not support or not isinstance(support, dict):
        return False
    # Loop through the support dict
    for key in support:
        # Keys should match exactly, even if no value is associated with it
        # The Keys are not optional
        if not set(support[key].keys()) == {'modifier', 'prefix', 'model', 'column', 'type'}:
            return False
        # There must be a non-null model
        if not support[key].get('model'):
            return False
        if not (support[key].get('column') or not isinstance(support[key].get('column'), list)) and not isinstance(
                support[key].get('column'), dict):  # Column can either be a list or a dict or System:Column key/values
            return False
        # These are the custom accepted types that drive filter and normalization actions downstream
        if not support[key].get('type') or support[key].get('type') not in ['bool', 'datetime', 'int',
                                                                            'string', 'timestamp', 'date',
                                                                            'numeric',
                                                                            'token']:
            return False
        # Supported modifiers must be supplied as a list
        modifier_list = support[key].get('modifier')
        if not isinstance(modifier_list, list):
            return False
        # Validate each modifier against dict of valid FHIR modifiers
        for m in modifier_list:
            if m not in fhir_modifiers.keys():
                return False
        # Supported prefixes must be supplied as a list
        prefix_list = support[key].get('prefix')
        if not isinstance(prefix_list, list):
            return False
        # Validate each prefix against dict of valid FHIR prefixes
        for p in prefix_list:
            if p not in fhir_prefixes.keys():
                return False
    # No issues - return True bool
    return True


def parse_fhir_search(args, base, model_support=None):
    """
    Function parse_fhir_search()
        Handles request URL parameters from a FHIR search endpoint and noramlizes / parses values to a fhir_search_spec
        dictionary that can be used to dynamically generate a SQLAlchemy query.  Examples the request args, the base
        model to which the FHIR resource endpoint is associated and a model_support dict which stores the supported
        search parameters for the given model.
    :param args:
        The requests.request.args associated with the FHIR API request
    :param base:
        The SQLAlchemy ORM model to which the FHIR Resource endpoint relates
    :param model_support:
        A dictionary that expresses which attributes related to the FHIR Resource may be used in search parameters.
        Defines the data-type of the searchable attributes
        Defines the modifier and prefixes that may be used in conjunction with the attribute during the search operation
        Maps the SQLAlchemy Model and model attribute (column) to which each search parameter may apply

        The dictionary passed to the model_support param is validated against the search_support_is_valid function

        Format:
        {
        # Top-level key.  Matches the parameter supported in search URL.
        'param_name':
                    {
                     # List of FHIR search Modifiers supported for param
                    'modifier': [],

                     # List of FHIR search Prefixes supported for param
                     'prefix': [],

                     # List of column names to which param applies for filtering and sorting.
                     # Column must match a valid column name for the associated SQLAlchemy model
                     # Multiple columns will cause filter operation to be applied to both columns
                     # with an OR condition between the outcome of each column operation.
                     # Ex: last_name,first_name will apply filter operation where last_name or first_name meet criteria
                     # all sort operations will be performed strictly on first column in the list of columns
                     'column': [],

                     # The flask_sqlalchemy declarative base model to which the operation / column should apply
                     'model' : Model,

                     # The data-type of the model.
                     # One of ['bool', 'datetime', 'int','string', 'timestamp', 'date', 'numeric','token']
                     'type' : ''
                     }
        }


        Example configuration:

        {'active': {'modifier': ['not'],
                    'prefix': [],
                    'model': Patient,
                    'column': ['active'],
                    'type': 'bool'},
         'birthdate': {'modifier': [],
                       'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                       'model': Patient,
                       'column': ['dob'],
                       'type': 'date'},
         'given': {'modifier': ['exact', 'contains', 'missing'],
                   'prefix': [],
                   'model': Patient,
                   'column': ['first_name', 'middle_name'],  # Will search both with or condition
                   'type': 'string'}
                }
        }

    :return:
        A dictionary which is  the translation of the FHIR Search parameters supplied via the request
        into a data structure that can be dynamically applied to an un-executed SQLAlchemy query.  Each
        dict in the list contains logically related attributes that are needed to apply a filter or sort
        operation to a query.

        {'key' :                    # Top level key = search parameter
            {'op': '__eq__',        # SQLAlchemy column operator
            'value': value,         # Value to be filtered / sorted on
            'model': model,         # SQLAlchemy ORM model to apply the search to
            'column': column}       # Name of column within ORM model on which to apply value and operator
        }


    """
    ##############################################################
    # FHIR Search Support Compilation
    ##############################################################
    default_support = {'_id': {'modifier': ['exact', 'not'],
                               'prefix': [],
                               'model': base,
                               'column': ['id'],
                               'type': 'int',
                               'validation': []},
                       '_lastUpdated': {'modifier': [],
                                        'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                                        'model': base,
                                        'column': ['updated_at'],
                                        'type': 'datetime',
                                        'validation': []}
                       }
    # Build one search support dictionary by combining the default and model support dicts
    if model_support and not search_support_is_valid(support=model_support):
        raise ValueError('Invalid model search support')
    support = {**default_support, **model_support}

    # Initialize the dict that will be generated as output
    fhir_search_spec = {}

    # Loop through args in request
    for arg in args:
        # Initialize parameters that may be assigned
        op = None
        value = None
        column = None
        value_forced_by_operator = False  # This is to track whether the operator determines the value

        arg_split = arg.split(':')  # Attempt to split args to determine if modifier exists
        search_key = arg_split[0]  # Get the parameter to which the search applies
        input_value = request.args.get(arg)  # Get the raw value for the parameter

        # Ignore parameters handled elsewhere with bundle and pagination decorators
        if search_key in ['page', '_count', '_format', '_summary']:
            continue

        ##############################################################
        # FHIR Sorting
        ##############################################################
        if search_key == '_sort' and input_value:
            sort_column = None
            sort_type = None

            # Sort values prefaced with '-' indicate descending sort is requested
            if input_value[0:1] == '-':
                sort_type = 'desc'
                input_value = input_value[1:]  # Get rid of that pesky '-' from the value

            # Now that we've handled the potential for a '-' in the value, check if the
            # value for the _sort param is in the support dictionary
            # If exists, create a fhir search spec with sort data
            if input_value in support.keys():
                sort_column = support[input_value].get('column')  # Lookup column by the value for sort
                if not sort_type:  # If not 'desc' set to 'asc'
                    sort_type = 'asc'

                # Set the data model for _sort
                fhir_search_spec[search_key] = {'op': sort_type,
                                                'model': support[input_value].get('model'),
                                                'column': sort_column}
            # Raise an error if attempting to sort by a param that is not supported by the model
            else:
                raise ValidationError('The sort key ({}) is not supported for this resource'.format(input_value))

            continue

        ##############################################################
        # FHIR Search Modifiers
        ##############################################################

        if search_key in support.keys():
            if not input_value:
                raise ValidationError(
                    'No value was supplied with parameter {}'.format(search_key))

            # Attempt to find and interpret search param modifiers like param:contains=value
            try:
                # Get the modifier, and check if that modifier is supported for the given param
                search_modifier = arg_split[1].lower().strip()
                if search_modifier in support[search_key].get('modifier'):

                    # Handle special syntax for :missing param which checks for Null / Not Null
                    if search_modifier == 'missing':
                        # Indicate the value type is forced by the param modifier
                        value_forced_by_operator = True
                        try:
                            # Make sure values for params with :missing modifier are booleans
                            value = validate_bool(value=input_value, error=True)
                            if isinstance(value, bool):
                                if value:
                                    op = 'is_'
                                    value = None
                                else:
                                    op = 'isnot'
                                    value = None
                        # Gotta use a boolean value for the missing modifier
                        except ValueError:
                            raise ValidationError(
                                'The value for parameter ({}) with modifier (missing) was ({}) and could not be validated as a boolean input for the search' \
                                    .format(search_key, input_value))

                    # Use the isnot SQLAlchemy operator for boolean value comparisons with :not modifier
                    elif search_modifier == 'not' and support[search_key].get('type') == 'bool':
                        op = 'isnot'

                    # Otherwise use the operators in the lookup dictionary and the value as-is
                    else:
                        op = fhir_modifiers.get(search_modifier)

                # Give a helpful error if the modifier is not supported by the model
                else:
                    raise ValidationError('The search parameter ({}) does not support the modifier ({})' \
                                          .format(search_key, search_modifier))

            # No search parameter modifier exists - carry on
            except IndexError:
                pass

            ##############################################################
            # FHIR Search Values & Prefixes by Type
            ##############################################################
            if not value_forced_by_operator:
                param_type = support[search_key].get('type')

                ##############################################################
                # FHIR Ordered Types - Check for Prefix
                ##############################################################
                if param_type in {'date', 'datetime', 'timestamp', 'numeric'}:
                    # Attempt to get first 2 characters as prefixes like 'gt'
                    try:
                        value_prefix = input_value[0:2].lower().strip()
                        if value_prefix in fhir_prefixes.keys():
                            input_value = input_value[2:]
                            op = fhir_prefixes.get(value_prefix)

                    # First 2 characters are not a known prefix - ignore
                    except IndexError:
                        pass

                ##############################################################
                # FHIR Boolean Value Handling
                ##############################################################
                if param_type == 'bool':
                    try:
                        value = validate_bool(value=input_value, error=True)
                    except ValueError:
                        raise ValidationError(
                            'The value for parameter ({}) was ({}) and could not be validated as a boolean input for the search' \
                                .format(search_key, input_value))

                ##############################################################
                # FHIR Datetime Value Handling
                ##############################################################
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

                ##############################################################
                # FHIR String Value Handling
                ##############################################################
                elif param_type == 'string':  # Deal with case comparison
                    input_value = unidecode.unidecode(input_value)  # Handle accents per FHIR
                    if op == 'ilike':  # Handles the :contains modifier for string parameters
                        value = '%' + str(input_value) + '%'
                    if not op:  # If no modifier is defined for string parameters a case-insensitive starts_with comp
                        op = 'ilike'
                        value = str(input_value) + '%'

                ##############################################################
                # FHIR Token / Code Value Handling
                ##############################################################
                elif param_type == 'token' and input_value:
                    # Tokens may be in the following formats
                    # [parameter]=[code]
                    # [parameter]=[system]|[code]
                    # [parameter]=|[code]
                    # [parameter]=[system]|
                    input_value_split = input_value.split('|')

                    # [parameter]=[code]
                    if len(input_value_split) == 1:
                        value = input_value_split[0]

                    # Handle system being present
                    elif len(input_value_split) == 2:
                        column_support = support[search_key].get('column')
                        value_system = input_value_split[0].strip()
                        # If system is present, system must be designated as key in k/v pairs of column list in
                        # the support dictionary
                        if not isinstance(column_support, dict) or value_system not in column_support.keys():
                            raise ValidationError(
                                'The search parameter ({}) does not support the system ({})'.format(search_key,
                                                                                                    value_system))
                        # Set column output to the column name, not the system name
                        column = [column_support.get(value_system)]
                        if input_value_split[1]:
                            value = input_value_split[1].strip()
                        else:
                            input_value = None  # So that None will be assigned with the if not Value catch-all
                    else:
                        raise ValidationError(
                            'The value for the token parameter {} included >1 (|) character'.format(search_key))

                # Take the raw value from the input if it hasn't been set yet
                if not value:
                    value = input_value

                # Assign the column if it hasn't been set yet
                if not column:
                    column = support[search_key].get('column')

            # Assign the default operator '__eq__'
            if not op:
                op = '__eq__'

            # Add to the output dictionary
            fhir_search_spec[search_key] = {'op': op,
                                            'value': value,
                                            'model': support[search_key].get('model'),
                                            'column': column}
    return fhir_search_spec


def fhir_apply_search_to_query(fhir_search_spec, base, query=None):
    """
    Take an un-executed SQLAlchemy query instance, a specification output from parse_fhir_search and a base
    ORM model to which to apply the query.  Apply filter and sort operations dynamically to the query and return
    the query ready for execution.

    :param fhir_search_spec:
        A dict of dicts that contains all of the information needed to construct a filter or order_by operation
        {'key' :                    # Top level key = search parameter from API call
            {'op': '__eq__',        # SQLAlchemy column operator
            'value': value,         # Value to be filtered / sorted on
            'model': model,         # SQLAlchemy ORM model to apply the search to
            'column': column}       # Name of column within ORM model on which to apply value and operator
        }

    :param query:
        Un-executed SQLAlchemy query object
        Will be initialized to base.query if missing

    :param base:
        The base SQLAlchemy ORM model to apply the search to

    :return:
        Un-executed SQLAlchemy query with filtering and sorting applied according to the input specification
    """
    # Initialize query if missing
    if not query:
        query = base.query

    ##############################################################
    # Loop through query search specification dicts
    ##############################################################
    executed_joins = []  # Keep track of models that have been joined already so you don't join twice
    for key in fhir_search_spec.keys():
        column_spec = fhir_search_spec[key]['column']
        model = fhir_search_spec[key]['model']

        # Execute a join if model does not match base model
        if model != base and model not in executed_joins:
            query = query.join(model)
            executed_joins.append(model)

        # Handle sort operations
        if key == '_sort':
            column = getattr(model, column_spec[0])
            op = fhir_search_spec[key]['op']
            query = query.order_by(getattr(column, op)())
            continue

        # Handle most common situation where only one model attribute must be considered for filtering
        if len(column_spec) == 1:
            column = getattr(model, column_spec[0])  # Get the column on the model
            op = fhir_search_spec[key]['op']  # Get the operator for the column
            value = fhir_search_spec[key]['value']  # Get the value from the dict
            query = query.filter(getattr(column, op)(value)) # Dynamically construct the query

        # Handle situations where >1 attribute must be considered in the operation
        # In this case, the operator and value will be applied to each attribute with OR logic
        # between them.  Ex:  column1 = value or column2 = value or column3 = value
        else:
            filter_list = [] # Initialize a list of filter statements that will be applied
            op = fhir_search_spec[key]['op']
            value = fhir_search_spec[key]['value']
            for col in column_spec:
                column = getattr(model, col)
                filt = getattr(column, op)(value)
                filter_list.append(filt)
            query = query.filter(or_(*filter_list))

    return query


def fhir_search(args, model_support, base, query):
    """
    Parse FHIR search
    Translate to something SQLAlchemy undestands
    Apply search to a base query and return it as un-executed
    :param args:
        The requests.request.args associated with the FHIR API request
    :param base:
        The SQLAlchemy ORM model to which the FHIR Resource endpoint relates
    :param model_support:
        A dictionary that expresses which attributes related to the FHIR Resource may be used in search parameters.
        Defines the data-type of the searchable attributes
        Defines the modifier and prefixes that may be used in conjunction with the attribute during the search operation
        Maps the SQLAlchemy Model and model attribute (column) to which each search parameter may apply

        The dictionary passed to the model_support param is validated against the search_support_is_valid function

        Format:
        {
        # Top-level key.  Matches the parameter supported in search URL.
        'param_name':
                    {
                     # List of FHIR search Modifiers supported for param
                    'modifier': [],

                     # List of FHIR search Prefixes supported for param
                     'prefix': [],

                     # List of column names to which param applies for filtering and sorting.
                     # Column must match a valid column name for the associated SQLAlchemy model
                     # Multiple columns will cause filter operation to be applied to both columns
                     # with an OR condition between the outcome of each column operation.
                     # Ex: last_name,first_name will apply filter operation where last_name or first_name meet criteria
                     # all sort operations will be performed strictly on first column in the list of columns
                     'column': [],

                     # The flask_sqlalchemy declarative base model to which the operation / column should apply
                     'model' : Model,

                     # The data-type of the model.
                     # One of ['bool', 'datetime', 'int','string', 'timestamp', 'date', 'numeric','token']
                     'type' : ''
                     }
        }


        Example configuration:

        {'active': {'modifier': ['not'],
                    'prefix': [],
                    'model': Patient,
                    'column': ['active'],
                    'type': 'bool'},
         'birthdate': {'modifier': [],
                       'prefix': ['gt', 'ge', 'lt', 'le', 'eq', 'ne'],
                       'model': Patient,
                       'column': ['dob'],
                       'type': 'date'},
         'given': {'modifier': ['exact', 'contains', 'missing'],
                   'prefix': [],
                   'model': Patient,
                   'column': ['first_name', 'middle_name'],  # Will search both with or condition
                   'type': 'string'}
                }
        }
    :param query:
        Un-executed SQLAlchemy query object
        Will be initialized to base.query if missing

    :return:
        Un-executed SQLAlchemy query with filtering and sorting applied according to the input specification
    """
    fhir_search_spec = parse_fhir_search(args=args, model_support=model_support, base=base)
    return fhir_apply_search_to_query(fhir_search_spec=fhir_search_spec, query=query, base=base)
