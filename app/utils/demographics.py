import re
from entropy import shannon_entropy
from uszipcode import ZipcodeSearchEngine
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from datetime import datetime


def normalize_phone(phone):
    __doc__ = """
    Utility function to normalize phone numbers.  

    PARAM: PHONE:  String representation of a phone number.

    1) If phone number is valid, it is returned in the format '(XXX) XXX-XXX'
    2) If no valid phone number is supplied, None is returned
    """
    if not phone:
        return None
    ph = re.compile(r'.*1?.*([1-9][0-9]{2}).*([0-9]{3}).*([0-9]{4}).*')
    n_phone = ph.match(phone)
    if not n_phone:
        return None
    else:
        return str('{}{}{}'.format(n_phone.group(1), n_phone.group(2), n_phone.group(3)))


def normalize_ssn(ssn):
    __doc__ = """
    Utility function to normalize social security numbers (SSN)

    PARAM SSN:
        Type: String
        The SSN to normalize    

    Function accepts any SSN string and, if determined to be valid, outputs 
    the SSN in the format 'XXX-XX-XXXX'

    If SSN argument is invalid, None is returned

    Invalid SSNs are:
        1) Not equal to 9 numeric digits in length
        2) Equal to known "bad_ssns" values like "123456789"
        3) Numbers with all 0's in any digit group like "000-XX-XXXX" or "XXX-00-XXXX" or "XXX-XX-0000"
        4) Numbers in first digit group between "900" and "999"
        5) Numbers with a Shannon Entropy value <.16 like "111-22-2222"
    """
    if not ssn:
        return None
    bad_ssns = ['123456789']
    numeric_digits = re.compile(r'[^0-9]+')
    ssn_digits = numeric_digits.sub('', ssn)
    if len(ssn_digits) != 9:
        ssn_digits = None
        return None
    elif ssn_digits:
        ssn_compile = re.compile(r'.*([0-8][0-9]{2}).*([0-9]{2}).*([0-9]{4}).*')
        n_ssn = ssn_compile.match(ssn_digits)
        if n_ssn:
            n_ssn_digits = str('{}{}{}'.format(n_ssn.group(1), n_ssn.group(2), n_ssn.group(3)))
            if (n_ssn_digits in bad_ssns) or (n_ssn.group(1) in ['666', '000']) or (n_ssn.group(2) in ['00']) or (
                        n_ssn.group(3) in ['0000']):
                return None
            elif shannon_entropy(n_ssn_digits) < .16:
                return None
            else:
                return str('{}{}{}'.format(n_ssn.group(1), n_ssn.group(2), n_ssn.group(3)))


def normalize_city_state(city=None, state=None):
    __doc__ = """
    Utility function that accepts string representations of city and state, and returns a tuple
    of a validated city and state value.  The tuple is returned as ("cityname", "statename", "zipcode"). If
    lookup fails for one or all three items a None object is returned in the tuple.
    """
    zipcode_search = ZipcodeSearchEngine()
    if state and city:
        try:
            city_state_zips = zipcode_search.by_city_and_state(city, state)
            if city_state_zips:
                zip_object = city_state_zips[0]
                single_zipcode = None
                if len(city_state_zips) == 1:
                    single_zipcode = zip_object.Zipcode
                return zip_object.City, zip_object.State, single_zipcode
        except(ValueError):
            return None, lookup_state(state), None
    elif state:
        return None, lookup_state(state), None


def lookup_state(state=None):
    zipcode_search = ZipcodeSearchEngine()
    state_zips = zipcode_search.by_state(state)
    state = state_zips[0]
    return state.State


def lookup_zipcode(zipcode):
    __doc__ = """Accepts a string value for a zipcode to lookup
    if matching zipcode is found a dictionary object for the zipcode
    including information about it is returned.  This is a uszipcode zipcode
    object.  If no zipcode is found, None is returned."""
    zipcode_search = ZipcodeSearchEngine()
    zipcode = zipcode_search.by_zipcode(zipcode)
    return zipcode


def normalize_zipcode(zipcode):
    n_zipcode = lookup_zipcode(zipcode)
    return n_zipcode.Zipcode


def normalize_address(address1=None, address2=None, city=None, state=None, zipcode=None):
    __doc__ = """
    Utility function to normalize five named parameters that comprise a physical address.  Returns a dictionary
    with keys "address1", "address2", "city", "state", "zipcode" which represents the normalized physical address.
    Uses supplied information to normalize address components.  

    If zipcode is supplied, zipcode is normalized to canonical list of zipcodes.  If match is found, the city
    and state attributes are set according to those associated with the zipcode.  If no match is found, the
    zipcode is set to None in the returned dictionary.

    If zipcode is not supplied, and state is supplied, the state name is validated and converted to standardized
    two character abbreviation in the resulting dictionary.

    If zipcode is not supplied, and city is supplied, the city name is accepted without validation.



    PARAM "address1"
    PARAM TYPE: str
    First address line of a physical address.  Default is None

    PARAM "address2"
    PARAM TYPE: str
    Second address line of a physical address.  Default is None

    PARAM "city"
    PARAM TYPE: str
    Name of the city for the physical address.  Default is None

    PARAM "state"
    PARAM TYPE: str
    State name for the physical address.  Uses state name lookup if necessary and allows 
    for fuzzy name matching and abbreviation lookup.  Default is None

    PARAM "zipcode"
    PARAM TYPE: str
    Zipcode component of a physical address.  Long or short form US zipcodes are accepted.  This input
    is validated against a canonical list of zipcodes in the US.
    """
    n_address_dict = {"address1": None, "address2": None, "city": None, "state": None, "zipcode": None}
    if zipcode:
        zip_object = lookup_zipcode(zipcode)
        if zip_object:
            n_address_dict["zipcode"] = zip_object.Zipcode
            n_address_dict["state"] = zip_object.State
            n_address_dict["city"] = (str(zip_object.City).upper())
    if address1:
        # TODO Address validation
        n_address_dict["address1"] = str(address1).upper().strip()
        n_address_dict["address2"] = str(address2).upper().strip()
    if (not n_address_dict.get("zipcode", None)) and state:
        n_city, n_state, n_zipcode = normalize_city_state(city=city, state=state)
        n_address_dict["state"] = n_state
        n_address_dict["city"] = str(n_city).upper()
        n_address_dict["zipcode"] = n_zipcode
        if not n_address_dict.get("city", None):
            n_address_dict["city"] = str(city).upper().strip()
    return n_address_dict


def normalize_name(name=None):
    __doc__ = """
    Utility Function to Normalize Names

    Any parentheses with contents should be removed. Any dashes,
    commas, single quotes or other characters should be replaced with null. 
    Final contents should be trimmed on both sides and in uppercase."
    """

    def remove_paren(value):
        paren_re = re.compile(r'\([^()]*(\)|$)')
        n_value = paren_re.sub('', value)
        while n_value != value:
            value = n_value
            n_value = paren_re.sub('', value)
        return value

    def remove_restricted_chars(value):
        restricted_re = re.compile("[,.'^*#&$@!%+]")
        value = restricted_re.sub('', value).strip()
        return value

    def finalize_output(value):
        value = value.strip().upper()
        return value

    if name:
        name = remove_paren(value=name)
        name = remove_restricted_chars(value=name).upper()
        name = finalize_output(value=name)

    return name


def normalize_lastname_suffix(last_name=None, suffix=None):
    __doc__ = """
    Utility function to normalize last names and suffix values
    If suffix is supplied, it is compared to accepted dictionary
    of suffix values.  If match is found, the normalized output is 
    accepted.
    
    If normalized suffix is not found, the lastname is evaluated for
    the inclusion of a suffix in the string.  If a valid suffix is found
    it is removed from the lastname and supplied as the suffix.
    
    All usual name normalization logic is applied to the lastname, where
    special characters are stripped, parenthetical text removed and result
    is trimmed of leading/trailing whitespace.  All text is output in uppercase
    
    Accepts two optional parameters:  lastname and suffix
    
    Returns a tuple in format of lastname, suffix.
    
    If either value is None, None is retured in the tuple
    """

    def strip_suffix(lastname=None, suffix=None):
        if not (lastname or suffix):
            return lastname, suffix
        suffix_dict = {'JR': 'JR', 'JUNIOR': 'JR', 'SR': 'SR', 'SENIOR': 'SR', 'I': 'I', 'II': 'II',
                       'III': 'III', 'IV': 'IV', '1ST': 'I', '2ND': 'II', '3RD': 'III', '4TH': 'IV'}
        if suffix:
            suffix = suffix_dict.get(suffix, None)

        if lastname:
            suffix_endings = frozenset(
                [' JR', ' JUNIOR', ' SR', ' SENIOR', ' I', ' II', ' III', ' IV', ' 1ST', ' 2ND', ' 3RD', ' 4TH'])

            for suff in suffix_endings:
                if lastname.endswith(suff):
                    if not suffix:
                        suffix = lastname[-len(suff):]
                        suffix = suffix.strip()
                    lastname = lastname[:-len(suff)]

        return lastname, suffix

    last_name = normalize_name(name=last_name)
    suffix = normalize_name(name=suffix)
    last_name, suffix = strip_suffix(lastname=last_name, suffix=suffix)

    return last_name, suffix


def normalize_email(email=None):
    if not email:
        return None
    email_re = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    validated_email = re.match(email_re, email)
    if not validated_email:
        return None
    else:
        return str(email).strip().upper()


def normalize_dob(dob=None):
    n_dob = None
    if not dob:
        return None
    if isinstance(dob, datetime):
        n_dob = dob
    if isinstance(dob, str):
        try:
            n_dob = dateparser.parse(dob, ignoretz=True)
        except ValueError:
            n_dob = None
    if n_dob:
        today = datetime.today()
        lower_limit = today + relativedelta(years=-130)
        if lower_limit <= n_dob <= today:
            return n_dob
        else:
            return None
    else:
        return None


def normalize_race(race=None):
    if not race:
        return None

    race = str(race).strip().upper()
    race_values = frozenset(["1002-5", "2028-9", "2054-5", "2076-8", "2131-1", "2106-3"])
    if race in race_values:
        return race

    race_dict = {"1002-5": frozenset(["AMERICAN INDIAN OR ALASKA NATIVE", "AI"]),
                 "2028-9": frozenset(["ASIAN", "AS"]),
                 "2054-5": frozenset(["BLACK OR AFRICAN AMERICAN", "B", "BL", "BLACK", "AFRICAN AMERICAN", "AA"]),
                 "2076-8": frozenset(
                     ["NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER", "HAWAIIAN", "NH", "PACIFIC ISLANDER", "PI"]),
                 "2131-1": frozenset(["OTHER RACE", "O", "OTHER", "OTH", "OT", "OR"]),
                 "2106-3": frozenset(["WHITE", "W", "WH", "WHI", "WHIT" "CAUCASIAN"])}

    for key in race_dict:
        if race in race_dict[key]:
            race = key

    if race in race_values:
        return race
    else:
        return None


def normalize_ethnicity(ethnicity=None):
    if not ethnicity:
        return None
    ethnicity = str(ethnicity).strip().upper()
    ethnicity_values = frozenset(["2135-2", "2186-5"])
    ethnicity_dict = {"2135-2": frozenset(["HISPANIC OR LATINO", "H", "HISPANIC", "HISP", "LATINO", "L", "LAT", "1"]),
                      "2186-5": frozenset(["NOT HISPANIC OR LATINO", "N", "NOT", "NOT HISPANIC", "NOT LATINO", "0"])}
    if ethnicity in ethnicity_values:
        return ethnicity

    for key in ethnicity_dict:
        if ethnicity in ethnicity_dict[key]:
            ethnicity = key

    if ethnicity in ethnicity_values:
        return ethnicity

    else:
        return None


def normalize_marital_status(status=None):
    if not status:
        return None
    status = str(status).strip().upper()
    status_values = frozenset(["N", "C", "D", "P", "I", "E", "G", "M", "O", "R", "A", "S", "U", "B", "T"])
    status_dict = {"N": frozenset(["ANNULLED"]),
                   "C": frozenset(["COMMON LAW"]),
                   "D": frozenset(["DIVORCED"]),
                   "P": frozenset(["DOMESTIC PARTNER"]),
                   "I": frozenset(["INTERLOCUTORY"]),
                   "E": frozenset(["LEGALLY SEPARATED"]),
                   "G": frozenset(["LIVING TOGETHER"]),
                   "M": frozenset(["MARRIED", "MAR"]),
                   "O": frozenset(["OTHER"]),
                   "R": frozenset(["REGISTERED DOMESTIC PARNTER"]),
                   "A": frozenset(["SEPARATED"]),
                   "S": frozenset(["SINGLE", "SIN"]),
                   "U": frozenset(["UNKNOWN", "UNK"]),
                   "B": frozenset(["UNMARRIED"]),
                   "T": frozenset(["UNREPORTED"]),
                   }
    if status in status_values:
        return status

    for key in status_dict:
        if status in status_dict[key]:
            status = key

    if status in status_values:
        return status

    else:
        return None


def normalize_deceased(value=None):
    if not value:
        return False
    if isinstance(value, bool):
        return value
    deceased_list = frozenset(["DECEASED", "DEAD", "DIED", "D", "1"])

    value = str(value).upper().strip()

    if value in deceased_list:
        return True
    else:
        return False
