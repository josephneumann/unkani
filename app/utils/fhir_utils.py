from fhirclient.models import humanname, fhirdate
from app.utils.type_validation import validate_datetime


def fhir_gen_humanname(use='official', first_name=None, last_name=None, middle_name=None, suffix=None, prefix=None):
    """
    Helper function to generate a fhirclient HumanName class object from standard person attributes
    :param use:
    :param first_name:
        String representation of person first name
    :param last_name:
        String representation of person last name
    :param middle_name:
        String representation of person middle name
    :param suffix:
        String representation of name suffix
    :param prefix:
        String representation of name prefix
    :return:
        fhirclient HumanName class object
    """
    hn = humanname.HumanName()
    if use:
        hn.use = use
    hn.family = last_name
    given_name = []
    if first_name:
        given_name.append(first_name)
    if middle_name:
        given_name.append(middle_name)
    if given_name:
        hn.given = given_name
    if suffix:
        hn.suffix = [suffix]
    if prefix:
        hn.prefix = [prefix]

    hn.text = '{}{}{}{}'.format(last_name + ',' if last_name else '',
                                ' ' + first_name if first_name else '',
                                ' ' + middle_name if middle_name else '',
                                ' ' + suffix if suffix else '')
    return hn


def fhir_gen_datetime(value=None, to_date=False, error_out=False):
    """
    :return:
        fhirclient.models.fhirdate.FHIRDate class object if it can be constructed
        If invalid datetime string is passed, DatetimeParseError is raised if error_out=True
    """
    dt = validate_datetime(value=value, to_date=to_date, error_out=error_out)
    fhir_date_obj = fhirdate.FHIRDate()
    if dt:
        fhir_date_obj.date = dt
        return fhir_date_obj
    fhir_date_obj.date = None
    return fhir_date_obj
