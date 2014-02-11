"""
microsoft.constants

Couldn't find a reference source for this anywhere except in raw sql queries of an example Microsoft 2012 database
"""

class FIELD_TYPE:
    pass


field_type_name = dict(
    (getattr(FIELD_TYPE, name, ''), name) for name in dir(FIELD_TYPE) if not name.startswith('_')
    )

reverse_field_type_name = dict(
    (name, getattr(FIELD_TYPE, name, '')) for name in dir(FIELD_TYPE) if not name.startswith('_')
    )

