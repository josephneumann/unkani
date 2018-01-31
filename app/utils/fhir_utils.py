from fhirclient.models import humanname


def generate_humanname(use='official', first_name=None, last_name=None, middle_name=None, suffix=None, prefix=None):
    hn = humanname.HumanName()
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
