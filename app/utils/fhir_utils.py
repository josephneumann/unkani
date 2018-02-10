from fhirclient.models import humanname, fhirdate
from datetime import datetime
from dateutil import parser as dateparser


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


def fhir_gen_datetime(dt=None, to_date=False):
    """
    Helper function to construct a valid fhirclient.models.fhirdate.FHIRDate class object
    from a datetime string or datetime object
    :param dt:
        A str or datetime type object representing a date
    :param to_date:
        If true, output is trimmed to a date.  If false, datetime timestamp is generated
        Default: False
    :return:
        fhirclient.models.fhirdate.FHIRDate class object if it can be contstructed
        If invalid datetime string is passed, ValueError is raised
    """
    if not isinstance(to_date, bool):
        raise TypeError('to_date param must be type bool')
    if not isinstance(dt, datetime):
        try:
            dt = dateparser.parse(str(dt), ignoretz=to_date)
        except ValueError:
            raise ValueError("An unknown string format for datetime was supplied")
    if dt:
        if to_date:
            dt = dt.date()
        fhir_date_obj = fhirdate.FHIRDate()
        fhir_date_obj.date = dt
        return fhir_date_obj
