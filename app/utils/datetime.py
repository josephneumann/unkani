from dateutil import parser as dateparser
from datetime import datetime


class DatetimeParseError(ValueError):
    """Custom exception for errors due to datetime parsing.  Subclass of ValueError"""
    pass


def datetime_handler(value=None, error_out=True, to_date=False):
    """
    Helper function to validate a datetime object or parse a valid date or datetime string into
    a datetime object
    :param value:
        A str or datetime type object representing a date
    :param to_date:
        If true, output is trimmed to a date.  If false, datetime timestamp is generated
        Default: False
    :param error_out:
        If true, exceptions are raised when datetime object cannot be constructed.
        If false, no exception is raised
        Default: False
    :return:
        datetime.datetime or datetime.date object
    """
    if not isinstance(to_date, bool):
        raise TypeError('to_date param must be type bool')
    if not isinstance(error_out, bool):
        raise TypeError('to_date param must be type bool')
    dt = None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = dateparser.parse(str(value), ignoretz=to_date)
        except ValueError:
            if error_out:
                raise DatetimeParseError("An unknown string format for datetime was supplied")
            else:
                pass
    if dt and to_date:
        dt = dt.date()
    return dt
