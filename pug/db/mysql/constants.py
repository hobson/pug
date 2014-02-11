"""
mysql.constants

>>> FIELD_TYPE.VAR_STRING
253
>>> FIELD_TYPE.STRING
254
>>> field_type_name[FIELD_TYPE.INT24]
'INT24'
>>> reverse_field_type_name['FLOAT']
4
"""

class FIELD_TYPE:
    BLOB = 252
    CHAR = 1
    DECIMAL = 0
    NEWDECIMAL = 246
    DATE = 10
    DATETIME = 12
    DOUBLE = 5
    FLOAT = 4
    INT24 = 9
    LONG = 3
    LONGLONG = 8
    SHORT = 2
    STRING = 254
    TIMESTAMP = 7
    TINY = 1
    TINY_BLOB = 249
    MEDIUM_BLOB = 250
    LONG_BLOB = 251
    VAR_STRING = 253
    
    # GIS constants
    GEOMETRY = 255

field_type_name = dict(
    (getattr(FIELD_TYPE, name, ''), name) for name in dir(FIELD_TYPE) if not name.startswith('_')
    )

reverse_field_type_name = dict(
    (name, getattr(FIELD_TYPE, name, '')) for name in dir(FIELD_TYPE) if not name.startswith('_')
    )

