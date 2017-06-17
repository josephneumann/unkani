import re
import random
from datetime import datetime, date
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta
from uszipcode import ZipcodeSearchEngine
from faker import Faker
from entropy import shannon_entropy


def normalize_phone(phone):
    """
    Utility function to normalize phone numbers.  

    :param phone: 
        Type: String
        Default: None
        Description: String representation of a phone number.
    :return: 
        1) If phone number is valid, it is returned in the format 'XXXXXXXXX'
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


def random_phone():
    """
    Returns a random phone number as a string in format XXXXXXXXXX
    """
    p = list('0000000000')
    p[0] = str(random.randint(1, 9))
    for i in [1, 2, 6, 7, 8]:
        p[i] = str(random.randint(0, 9))
    for i in [3, 4]:
        p[i] = str(random.randint(0, 8))
    if p[3] == p[4] == 0:
        p[5] = str(random.randint(1, 8))
    else:
        p[5] = str(random.randint(0, 8))
    n = range(10)
    if p[6] == p[7] == p[8]:
        n = [i for i in n if i != p[6]]
    p[9] = str(random.choice(n))
    p = ''.join(p)
    return str(p[:3] + p[3:6] + p[6:])


def format_phone(phone=None):
    """
    Utility function to return a properly formatted phone number
    
    :param phone: 
        Type: STR
        Default: None
        Description: Any phone number that requires formatting
    :return: 
        Type: String
        A phone number in format (XXX) XXX-XXXX
        
    """
    if not phone:
        return None
    ph = re.compile(r'.*1?.*([1-9][0-9]{2}).*([0-9]{3}).*([0-9]{4}).*')
    n_phone = ph.match(phone)
    if not n_phone:
        return None
    else:
        return str('({}) {}-{}'.format(n_phone.group(1), n_phone.group(2), n_phone.group(3)))


def normalize_ssn(ssn):
    """
    Utility function to normalize social security numbers (SSN)

    :param ssn: 
        Type: String
        Default: None
        Description: The SSN to normalize   
        
    :return: 
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


def random_ssn():
    """
    Utility function to generate a random social security number as a string
    SSN is formatted as XXX-XX-XXXX
    """
    fake = Faker()
    return fake.ssn()


def format_ssn(ssn=None):
    """
    Utility function to return a properly formatted social security number (SSN)
    
    :param ssn: 
        Type: String
        Default: None
        Description: Any social security number
    :return: 
        If a valid SSN is provided, returns SSN in format XXX-XX-XXXX
        Otherwise returns None
    """
    if not ssn:
        return None
    ssn_compile = re.compile(r'.*([0-8][0-9]{2}).*([0-9]{2}).*([0-9]{4}).*')
    n_ssn = ssn_compile.match(ssn)
    if n_ssn:
        return str('{}-{}-{}'.format(n_ssn.group(1), n_ssn.group(2), n_ssn.group(3)))


def normalize_city_state(city=None, state=None):
    """
    Utility function that accepts string representations of city and state, and returns a tuple
    of a validated city, state and zipcode value.
    
    :param city:
        Type: str
        Description: Name of a city to lookup.  Default is None
    :param state:
        Type: str
        Description: Name or abbreviation of a US state to lookup.  Default is None
        
    :return:
        Function accepts a city and state combination to lookup.  The city and state combination is matched against a 
        database of all US cities and states.  If a valid match is found, a tuple with the city and state name are returned.
        If just one zipcode exists for that city and state combination, a zipcode is also returned.  If multiple zipcodes
        match the city and state combination, then None is returned as the zipcode value in the tuple.
        
        The tuple is returned as ("cityname", "statename", "zipcode"). If lookup fails for one or all three items a None 
        object is returned in the tuple.
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
        except ValueError:
            return None, lookup_state(state), None
    elif state:
        return None, lookup_state(state), None


def lookup_state(state=None):
    """
    Utility function that accepts any valid string representation of a US state and returns a normalized two
    character abbreviation of the state.
    
    :param state:
        Type: String
        Default: None
        Description: String representation of a US state
    
    :return:
        If a valid US state is found, the two character state abbreviation is returned.
        Otherwise, None is returned
    """
    zipcode_search = ZipcodeSearchEngine()
    try:
        state_zips = zipcode_search.by_state(state)
        if state:
            state = state_zips[0]
            return state.State
        else:
            return None
    except TypeError:
        print("Invalid data type provided to lookup state function.")


def lookup_zipcode_object(zipcode):
    """
    Utility function to lookup a uszipcode zipcode object based on a zipcode string.
    
    :param zipcode:
        Type: String
        Default: None
        A string value for a zipcode to lookup
        
    :return:
        If matching zipcode is found a dictionary object for the zipcode including information about it is returned.  
        This is a uszipcode zipcode object.  
        
        If no zipcode is found, None is returned.
    """
    zipcode_search = ZipcodeSearchEngine()
    zipcode = zipcode_search.by_zipcode(zipcode)
    return zipcode


def normalize_zipcode(zipcode):
    """
    A utility function used to validate an normalize a zipcode.  Returns a zipcode as a string
    
    :param zipcode:
        Type: String
        Default: None
        A string value for a zipcode to lookup
        
    :return
        If a valid zipcode is matched, the zipcode is returned as a string
        Otherwise, None is returned
    """
    n_zipcode = lookup_zipcode_object(zipcode)
    return n_zipcode.Zipcode


def random_zipcode(number=1, potential_matches=1000, string_only=True):
    """
    Utility function to generate random zipcodes.  
    Randomly generates an object from the top 'potential_matches' zipcodes by population.
    
    USAGE NOTES:
    When generating random zipcodes, it is best to use this function to generate the number of results  you need,
    and then manipulate the returned list, rather than calling this function for each zipcode required.  
    Repeated calls to this function will repeat the generation of a list of 1000 zipcodes and affect performance.
      
    :param number:
        TYPE: int - positive values only
        DESCRIPTION: The number of zipcodes to randomly generate
        DEFAULT: 1
    
    :param string_only:
        TYPE: bool
        DESCRIPTION: When True, results are returned as string zipcodes.  When False, uszipcode.zipcode type objects
            are returned.  zipcode.Zipcode method can be used to return zipcode.  Other methods for city, state etc.
            also exist and can be used.
        DEFAULT: True
        
    :param potential_matches:
        TYPE: int (between 1 - 43000)
        DESCRIPTION:  The number of zipcodes to be returned from the entire list of US zipcodes ordered by population
            descending.  This number determines the set of zipcodes to randomly select from.  
        DEFAULT: 1000
    
    :return:
        A list of zipcode strings or objects
        

    """
    try:
        number = int(number)
        if number < 1:
            raise ValueError("A base 10 integer > 0 must be supplied to param 'number'.")

        potential_matches = int(potential_matches)
        if potential_matches < 1000:
            raise ValueError("A base 10 integer > 999 must be supplied to param 'potential_matches'.")

        string_only = bool(string_only)

        search = ZipcodeSearchEngine()
        res = search.by_population(lower=0, upper=999999999, sort_by="Population", ascending=False,
                                   returns=potential_matches)
        zipcode_list = []
        for x in range(0, number):
            zipcode = random.choice(res)
            if string_only:
                zipcode_list.append(zipcode.Zipcode)
            else:
                zipcode_list.append(zipcode)
        return zipcode_list
    except ValueError:
        print("""Please input an integer value for the parameter 'number' and parameter 'potential_matches'.  
        Please input a bool value for param 'string_only'.""")


def random_address_lines():
    """
    Utility function used to generate random address line values.
    Uses the python faker module to generate a random address1 and address2 value
    
    :return:
        Returns a tuple of two strings in format ("address1","address2")
        address1 is always populated, address2 is sometimes None
    """
    fake = Faker()
    addr1 = str(fake.street_address()).upper()
    addr2 = None
    if random.random() > 0.7 and not re.search(r'( APT.| APT | SUITE)+', addr1):
        addr2 = str(fake.secondary_address()).upper()
    return addr1, addr2


def normalize_address(address1=None, address2=None, city=None, state=None, zipcode=None):
    """
    Utility function to normalize five named parameters that comprise a physical address.  

    :param address1:
        Type: str
        First address line of a physical address.  Default is None

    :param address2
        Type: String
        Second address line of a physical address.  Default is None

    :param city:
        Type: String
        Name of the city for the physical address.  Default is None

   :param state:
        Type: String
        State name for the physical address.  Uses state name lookup if necessary and allows 
        for fuzzy name matching and abbreviation lookup.  Default is None

    :param zipcode:
        Type: String
        Zipcode component of a physical address.  Long or short form US zipcodes are accepted.  This input
        is validated against a canonical list of zipcodes in the US.
        
    :return:
        Returns a dictionary with keys "address1", "address2", "city", "state", "zipcode" which represents the 
        normalized physical address.
        
        Uses supplied information to normalize address components.  

        If zipcode is supplied, zipcode is normalized to canonical list of zipcodes.  If match is found, the city
        and state attributes are set according to those associated with the zipcode.  If no match is found, the
        zipcode is set to None in the returned dictionary.
    
        If zipcode is not supplied, and state is supplied, the state name is validated and converted to standardized
        two character abbreviation in the resulting dictionary.
    
        If zipcode is not supplied, and city is supplied, the city name is accepted without validation.
    """
    n_address_dict = {"address1": None, "address2": None, "city": None, "state": None, "zipcode": None}
    if zipcode:
        zip_object = lookup_zipcode_object(zipcode)
        if zip_object:
            n_address_dict["zipcode"] = zip_object.Zipcode
            n_address_dict["state"] = zip_object.State
            n_address_dict["city"] = (str(zip_object.City).upper())
    if address1:
        n_address_dict["address1"] = str(address1).upper().strip()
    if address2:
        n_address_dict["address2"] = str(address2).upper().strip()
    if (not n_address_dict.get("zipcode", None)) and state:
        n_city, n_state, n_zipcode = normalize_city_state(city=city, state=state)
        n_address_dict["state"] = n_state
        n_address_dict["city"] = str(n_city).upper()
        n_address_dict["zipcode"] = n_zipcode
        if not n_address_dict.get("city", None):
            n_address_dict["city"] = str(city).upper().strip()
    return n_address_dict


def random_full_address(number=1):
    """
    Utility function used to generate one or many random full addresses.
    :param number:
        Type: Int
        Default: 1
        Description: Number of random addresses to generate
    :return:
        Returns a list of dicts which contain key-value pairs of full address components.
        Example: [{"address1":"123 MAIN ST", "address2":"APT 1", "city":"MADISON", "state":"WI", "zipcode":"53703"}]
    """
    number = int(number)
    if number < 10:
        potential_matches = 1000
    else:
        potential_matches = 5000
    zipcode_list = random_zipcode(number=number, string_only=False, potential_matches=potential_matches)
    result = []
    for x in range(0, number):
        zip = zipcode_list.pop(0)
        add1, add2 = random_address_lines()
        add_dict = {"address1": add1, "address2": add2, "zipcode": zip.Zipcode, "city": str(zip.City).upper(),
                    "state": zip.State}
        result.append(add_dict)
    if result:
        return result
    else:
        return None


def normalize_name(name=None):
    """
    Utility Function to Normalize Names
    
    :param name:
        Type: String
        A name to normalize and output

    :return:
        Returns a 'normalized' name string:
            Any parentheses with contents will be removed. 
            Any dashes, commas, single quotes or other characters will be removed. 
            Final contents should be trimmed on both sides and in uppercase.
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


def random_first_name(sex=None):
    """
    Utility function to generate a random first name string
    :param sex: 
        Type: char(1) from set ['M','F']
        Default: None
        Description: Either None, 'M' or 'F'.  Determines sex of name to return
    :return: 
        If no sex is supplied, a random sex is chosen and corresponding gender's random first name is returned
        If a sex is supplied, a first name appropriate for that gender is returned

    """
    fake = Faker()
    if not sex:
        sex = random.choice(["M", "F"])
    if sex == "M":
        return str(fake.first_name_male()).upper()
    else:
        return str(fake.first_name_female()).upper()


def normalize_lastname_suffix(last_name=None, suffix=None):
    """
    Utility function to normalize last names and suffix values
    
    :param last_name:
        Type: String
        Last name to normalize.  Default is None
        
    :param suffix:
        Type: String
        Last name suffix to normalize along with last name.
    
    :return:
        If suffix is supplied, it is compared to accepted dictionary
        of suffix values.  If match is found, the normalized output is 
        accepted.
    
        If normalized suffix is not found, the lastname is evaluated for
        the inclusion of a suffix in the string.  If a valid suffix is found
        it is removed from the lastname and supplied as the suffix.
    
        All usual name normalization logic is applied to the lastname, where
        special characters are stripped, parenthetical text removed and result
        is trimmed of leading/trailing whitespace.  All text is output in uppercase
    
        Returns a tuple in format of lastname, suffix.
        
        If either value is None, None is returned in the tuple
    """

    def strip_suffix(lastname=None, suffix=None):
        if not (lastname or suffix):
            return lastname, suffix
        suffix_dict = {'JR': 'JR', 'JUNIOR': 'JR', 'SR': 'SR', 'SENIOR': 'SR', 'I': 'I', 'II': 'II',
                       'III': 'III', 'IV': 'IV', '1ST': 'I', '2ND': 'II', '3RD': 'III', '4TH': 'IV',}
        if suffix:
            suffix = suffix_dict.get(suffix, None)

        if lastname:
            suffix_endings = {' JR', ' JUNIOR', ' SR', ' SENIOR', ' I', ' II', ' III', ' IV', ' 1ST', ' 2ND', ' 3RD',
                              ' 4TH'}

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


def random_suffix():
    """
    Utility function to generate a random valid suffix
    """
    suffix_values = ["JR", "SR", "I", "II", "III", "IV"]
    if random.random() > 0.9:
        return random.choice(suffix_values)
    else:
        return None


def random_last_name():
    """Utility function to generate a random last name string"""
    fake = Faker()
    return str(fake.last_name()).upper()


def random_password():
    """
    Returns a random password as a string.
    Password is comprised of random integer concatentated with two random lorem ipsum words
    """
    fake = Faker()
    random_number = str(random.randint(0, 1000))
    password = fake.word() + random_number + fake.word()
    return str(password)


def normalize_email(email=None):
    """
    Utility function to validate whether a given string input is an email address and normalize the output by trimming
    leading and trailing whitespaces and converting the resulting string to upper case.
    :param email: 
        Type: String
        Default: None
        A string representation of an email address.  This is the email address to be validated / normalized
    :return:
        If email is None, returns None
        If email exists and does not pass regex validation, returns None
        If email exists and passes regex validation, rerturns email in uppercase and trimmed
    """
    if not email:
        return None
    email_re = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    validated_email = re.match(email_re, email)
    if not validated_email:
        return None
    else:
        return str(email).strip().upper()


def random_email():
    """
    Utility function to return a random email
    
    :return: 
        Returns an email with "@EXAMPLE.*" as the domain name pattern
    """
    fake = Faker()
    return str(fake.safe_email()).upper()


def normalize_dob(dob=None, max_age=130):
    """
    Utility function to normalize a person's date of birth (DOB).  Uses dateutil library to parse all possible
    date values into a datetime.date object.
    
    :param dob: 
        Type: String or Datetime or Date
        A representation of a persons date of birth    
        
    :param max_age: 
        Type: Integer
        The number of years, when substracted from the current date, to set as the farthest back plausible date for
        a date of birth.  Essentially the lower bound of the result.  Default == 130
        
    :return: 
        If dateutil.parser can extract a Datetime from param 'dob' and that datetime value is within the past 
        'year_lookback' years, then a datetime.Date object is returned
        
        Otherwise, None is returned
    """
    n_dob = None
    if not dob:
        return None
    else:
        dob = str(dob)
    if isinstance(dob, str):
        try:
            n_dob = dateparser.parse(dob, ignoretz=True)
        except ValueError:
            n_dob = None
    if n_dob:
        today = datetime.today()
        lower_limit = today + relativedelta(years=-max_age)
        if lower_limit <= n_dob <= today:
            return n_dob
        else:
            return None
    else:
        return None


def random_dob():
    """
    Utility function to generate a random date of birth (DOB)
    
    :return:
        Returns a random DOB as a datetime.date object.
        Lower Limit = Today - 100 years
        Upper Limit = Today - 18 years
    """
    current_date = datetime.today().date()
    start_date = (current_date + relativedelta(years=-100)).toordinal()
    end_date = (current_date + relativedelta(years=-18)).toordinal()
    dob = date.fromordinal(random.randint(start_date, end_date))
    return dob


def normalize_race(race=None):
    """
    Utility function to normalize string representations of race to the CDC Race Category codeset.  
    Value set OID == 2.16.840.1.114222.4.11.836
    
    :param race:
        Type: str
        Description: A representation of a person's race. Default is None
        
    :return: 
        If 'race' is None, returns None
        If 'race' is in CDC race category set, returns 'race'
        If 'race' lookup succeeds from dictionary 'race_dict', the top-level key of the dictionary is returned
        If 'race' is not None and lookup in 'race_dict' fails, returns None
    """
    if not race:
        return None

    race = str(race).strip().upper()
    race_values = {"1002-5", "2028-9", "2054-5", "2076-8", "2131-1", "2106-3"}

    if race in race_values:
        return race

    race_dict = {"1002-5": {"AMERICAN INDIAN OR ALASKA NATIVE", "AI"},
                 "2028-9": {"ASIAN", "AS"},
                 "2054-5": {"BLACK OR AFRICAN AMERICAN", "B", "BL", "BLACK", "AFRICAN AMERICAN", "AA"},
                 "2076-8": {"NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER", "HAWAIIAN", "NH", "PACIFIC ISLANDER", "PI"},
                 "2131-1": {"OTHER RACE", "O", "OTHER", "OTH", "OT", "OR"},
                 "2106-3": {"WHITE", "W", "WH", "WHI", "WHIT" "CAUCASIAN"}}

    for key in race_dict:
        if race in race_dict[key]:
            race = key

    if race in race_values:
        return race
    else:
        return None


def random_race():
    """
    Utility function to generate a random string value from the CDC Race Category codeset.
    Value set OID == 2.16.840.1.114222.4.11.836
    """
    race_values = ["1002-5", "2028-9", "2054-5", "2076-8", "2131-1", "2106-3"]
    return random.choice(race_values)


def normalize_ethnicity(ethnicity=None):
    """
    Utility function to normalize string representations of ethnicity categories
    Uses CDC ethnicity category value set OID == 2.16.840.1.114222.4.11.837
    Hispanic or Latino vs Not Hispanic or Latino
    
    :param ethnicity: 
        Type: String or Bool
        Default: None
        Description: A representation of ethnicity to be normalized
        
    :return:
        If 'ethnicity' is type String and input exists in CDC Ethnicity codeset, returns ethnicity code
        If 'ethnicity' is type String and lookup succeeds in 'ethnicity_dict', returns top level key of dict
        If 'ethnicity' is type Boolean, if True returns code for Hisp/Lat, if False, returns code for Not Hisp/Lat
        If 'ethnicity' is none, returns None
        If 'ethnicity' is not type Bool, and String lookup fails, returns None
    """
    if isinstance(ethnicity, bool):
        if ethnicity:
            return "2135-2"
        else:
            return "2186-5"
    if not ethnicity:
        return None
    ethnicity = str(ethnicity).strip().upper()
    ethnicity_values = {"2135-2", "2186-5"}
    ethnicity_dict = {
        "2135-2": {"HISPANIC OR LATINO", "H", "HISPANIC", "HISP", "LATINO", "L", "LAT"},
        "2186-5": {"NOT HISPANIC OR LATINO", "N", "NOT", "NOT HISPANIC", "NOT LATINO", "NOT HISP", "NOT LAT"}
    }
    if ethnicity in ethnicity_values:
        return ethnicity

    for key in ethnicity_dict:
        if ethnicity in ethnicity_dict[key]:
            ethnicity = key

    if ethnicity in ethnicity_values:
        return ethnicity

    else:
        return None


def random_ethnicity():
    """
    Utility function to generate a random ethnicity value from the CDC ethnicity category codeset

    :return: 
        Either "2135-2" for Hispanic or Latino or "2186-5" for Not Hispanic or Latino
    """
    ethnicity_values = ["2135-2", "2186-5"]
    return random.choice(ethnicity_values)


def normalize_marital_status(status=None):
    """
    Utility function to normalize a string representation of marital status to the HL7 Marital Status codeset.
    Value set OID == 2.16.840.1.114222.4.11.809
    
    :param status: 
        Type: String
        Default: None
        Description:  String representation of marital status.  May contain Hl7 Marital Status code or string
            representation of a marital status category
    :return: 
        If 'status' is char(1) and in the HL7 codeset, the same Hl7 code is returned
        If 'status' is in 'status_dict', the top level key (HL7 code) of the matching status is returned
        If 'status' cannot be found in lookup dict, returns None
        If 'status' is None, returns None
    """
    if not status:
        return None
    status = str(status).strip().upper()
    status_values = {"N", "C", "D", "P", "I", "E", "G", "M", "O", "R", "A", "S", "U", "B", "T"}
    status_dict = {"N": {"ANNULLED", "ANNULL"},
                   "C": {"COMMON LAW", "CL"},
                   "D": {"DIVORCED", "DIV", "DVC"},
                   "P": {"DOMESTIC PARTNER", "DP"},
                   "I": {"INTERLOCUTORY"},
                   "E": {"LEGALLY SEPARATED", "LS"},
                   "G": {"LIVING TOGETHER", "LT"},
                   "M": {"MARRIED", "MAR", "M."},
                   "O": {"OTHER", "OTH"},
                   "R": {"REGISTERED DOMESTIC PARNTER", "RDP"},
                   "A": {"SEPARATED", "SEP"},
                   "S": {"SINGLE", "SIN", "SING", "S"},
                   "U": {"UNKNOWN", "UNK", "N/A"},
                   "B": {"UNMARRIED"},
                   "T": {"UNREPORTED"},
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


def random_marital_status():
    """Utility function to randomly return one of the three most common marital status codes from the HL7 Marital
    Status codeset OID == 2.16.840.1.114222.4.11.809
    
    :return:
        "D" for divorced
        "M" for married
        "S" for single
    """
    status_values = ["D", "M", "S"]
    return random.choice(status_values)


def normalize_deceased(value=None):
    """
    Utility function to normalize a deceased status to a boolean representation.
    
    :param value: 
        Type: String or Bool
        Default: None
        Description:  Text representation of a deceased status or boolean for True = Deceased, False = Alive
        
    :return:
        If 'value' is type Bool returns 'value'
        If 'value' is type String and 'value' is in set 'deceased_list' returns True.
        If 'value' is type String and 'value' is not in set 'deceased_list' returns False
        If 'value' is None, returns None
    """
    if isinstance(value, bool):
        return value
    if not value:
        return False
    deceased_list = {"DECEASED", "DEAD", "DIED", "D"}

    value = str(value).upper().strip()

    if value in deceased_list:
        return True
    else:
        return False


def random_deceased():
    """
    Utility function to randomly return a boolean status for deceased.  
    99% chance that function returns False.
    01% chance that function returns True.
    
    :return: 
        Boolean representation of deceased status with high likelihood of False
    """
    if random.random() < 0.99:
        return False
    else:
        return True


def normalize_sex(sex=None):
    """
    Utility function to normalize a string representation of a person's gender to the approved char(1) representation
    listed below:
        "F" - Female
        "M" - Male
        "O" - Other
        
    A None / Null status is used to represent unknown genders rather than a designator "U"
    
    :param sex: 
        Type: String
        Default: None
        Description:  Any string representation of a person's gender that needs to be normalized
        
    :return: 
        If 'sex' is not type String, returns None
        If 'sex' is in approved sets of female, male or other values, returns "F", "M" or "O", respectively
        If 'sex' is type string and not in approved sets of values, returns None
    """
    if not isinstance(sex, str):
        return None
    else:
        female_values = {"F", "FEMALE", "WOMAN", "GIRL"}
        male_values = {"M", "MALE", "MAN", "BOY"}
        other_values = {"O", "OTHER", "N/A"}
        sex = str(sex).upper().strip()
        if sex in female_values:
            return 'F'
        if sex in male_values:
            return 'M'
        if sex in other_values:
            return 'O'
        else:
            return None


def random_sex():
    """
    A simple utility function to randomly return either "M" or "F" for gender
    
    :return: 
        "M" or "F"
    """
    if random.randint(0, 1):
        return "M"
    else:
        return "F"


def random_description(max_chars=200):
    """
    Utility function to generate a random 'lorem ipsum' style description text
    
    :param max_chars: 
        Type: Integer
        Default: 200
        Description:  Number of characters to return in randomly generated description
        
    :return:
        String description of length == 'max_chars' in 'lorem ipsum' style.
        Example with default 200 chars
            "Quas dignissimos provident debitis porro. Corporis maxime maxime repellendus vitae. 
            Molestiae placeat repellendus ullam rerum provident impedit velit perspiciatis."
    """
    try:
        max_chars = int(max_chars)
        fake = Faker()
        return fake.text(max_nb_chars=max_chars)
    except TypeError:
        print("Input for max_chars param could not be cast to an integer.")


def random_demographics(number=1):
    """
    Command line function to be used to generate random demographics.  Uses random_* functions to generate a list of
    dictionaries which contain common demographic values.
        
    :param number: 
        Type: Integer
        Default: 1
        Description:  A positive integer value that indicates the number of random demographic dictionaries to generate
        
    :return: 
        Returns a list of length == 'number' of demographic dictionaries. [{}.{},..]
        Demographic dictionaries contain key-value pairs of demographic elements.
        
        Example Demographic Dict:
        {'address1': '2389 FORD KEYS', 'ssn': '163-98-2131', 'cell_phone': '5421141524', 'race': '1002-5',
        'suffix': None, 'first_name': 'EDUARDO', 'deceased': False, 'address2': None, 'last_name': 'TAYLOR',
        'home_phone': '2686516100', 'ethnicity': '2135-2', 'dob': datetime.date(1945, 5, 3),
        'middle_name': 'ALEXANDER', 'zipcode': '78660', 'sex': 'M', 'work_phone': '1013348306',
        'state': 'TX', 'email': 'LORI58@EXAMPLE.NET', 'city': 'PFLUGERVILLE', 'marital_status': 'D'}
        
    """
    try:
        number = int(number)
        if number < 1:
            print("Invalid value passed as argument for 'number'.  Must be a positive integer of base 10.")
    except ValueError:
        print("Invalid value passed as argument for 'number'.  Must be an integer of base 10.")

    print("Creating random addresses...")
    address_list = random_full_address(number=number)
    result = []

    print("Creating demographics for each random entity...")
    print(number, end='...', flush=True)
    for x in range(0, number):
        sex = random_sex()
        first_name = random_first_name(sex=sex)
        middle_name = random_first_name(sex=sex)
        last_name = random_last_name()
        suffix = random_suffix()
        ssn = random_ssn()
        home_phone = random_phone()
        cell_phone = random_phone()
        work_phone = random_phone()
        email = random_email()
        dob = random_dob()
        deceased = random_deceased()
        marital_status = random_marital_status()
        race = random_race()
        ethnicity = random_ethnicity()

        demo_dict = {"first_name": first_name, "last_name": last_name, "middle_name": middle_name, "dob": dob,
                     "sex": sex, "ssn": ssn, "home_phone": home_phone, "cell_phone": cell_phone,
                     "work_phone": work_phone, "email": email, "deceased": deceased,
                     "suffix": suffix, "marital_status": marital_status, "race": race,
                     "ethnicity": ethnicity}
        demo_dict.update(address_list.pop(0))
        result.append(demo_dict)
        print("{}".format(int(number) - len(result)), end='...', flush=True)

    if result:
        print()
        print("Random demographic library of {} entries created...".format(number))
        return result
    else:
        return None
