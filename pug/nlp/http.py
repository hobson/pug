"""Functions for manipulating and composing http-protocol traffic

* simplify_get: eliminate empty and/or redundant HTTP GET parameters from a request dict

"""

import datetime

def simplify_get(get_dict, keys_to_del=None, datetime_to_date=True):
    """Delete any GET request key/value pairs if the value is an empty string or list.

    Delete any time information from datetimes if the time is 00:00:00.

    Example:
      >>> simplify_get({'a':1, 'b':0.0, 'c':None, 'd':[]},keys_to_del=['a']) == {'b': 0.0}
      True
    """
    keys_to_del = set(keys_to_del or ())
    get_dict = dict(get_dict.items())
    for k, v in get_dict.iteritems():
        if not v and v != 0 and v != False:
            keys_to_del.add(k)
        if datetime_to_date and isinstance(v, datetime.datetime) and not (v.hour or v.minute or v.second):
            get_dict[k] = datetime.date(v.year, v.month, v.day)
    for k in keys_to_del:
        if k in get_dict:
            del(get_dict[k])

    return get_dict