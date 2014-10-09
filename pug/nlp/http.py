"""Functions for manipulating and composing http-protocol traffic"""


def simplify_get(get_dict, keys_to_del=None):
    """Delete any GET request key/value pairs if the value is an empty string or list.

    Example:
      >>> simplify_get({'a':1, 'b':0.0, 'c':None, 'd':[]},keys_to_del=['a']) == {'b': 0.0}
      True
    """
    keys_to_del = set(keys_to_del or ())
    get_dict = dict(get_dict.items())
    for k, v in get_dict.iteritems():
        print k, v
        if not v and v != 0 and v != False:
            keys_to_del.add(k)
    for k in keys_to_del:
        if k in get_dict:
            del(get_dict[k])

    return get_dict