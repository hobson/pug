"""
microsoft.constants

Couldn't find a reference source for this anywhere except in raw sql queries of an example Microsoft 2012 database
"""

class FIELD_TYPE_NUM:
    pass


field_type_name = dict(
    (getattr(FIELD_TYPE_NUM, name, ''), name) for name in dir(FIELD_TYPE_NUM) if not name.startswith('_')
    )

reverse_field_type_name = dict(
    (name, getattr(FIELD_TYPE_NUM, name, '')) for name in dir(FIELD_TYPE_NUM) if not name.startswith('_')
    )


# django_field = {
#     FIELD_TYPE_NUM.BLOB: 'TextField',
#     FIELD_TYPE_NUM.CHAR: 'CharField',
#     FIELD_TYPE_NUM.DECIMAL: 'DecimalField',
#     FIELD_TYPE_NUM.NEWDECIMAL: 'DecimalField',
#     FIELD_TYPE_NUM.DATE: 'DateField',
#     FIELD_TYPE_NUM.DATETIME: 'DateTimeField',
#     FIELD_TYPE_NUM.DOUBLE: 'FloatField',
#     FIELD_TYPE_NUM.FLOAT: 'FloatField',
#     FIELD_TYPE_NUM.INT24: 'IntegerField',
#     FIELD_TYPE_NUM.LONG: 'IntegerField',
#     FIELD_TYPE_NUM.LONGLONG: 'IntegerField',
#     FIELD_TYPE_NUM.SHORT: 'IntegerField',
#     FIELD_TYPE_NUM.STRING: 'CharField',
#     FIELD_TYPE_NUM.TIMESTAMP: 'DateTimeField',
#     FIELD_TYPE_NUM.TINY: 'IntegerField',
#     FIELD_TYPE_NUM.TINY_BLOB: 'TextField',
#     FIELD_TYPE_NUM.MEDIUM_BLOB: 'TextField',
#     FIELD_TYPE_NUM.LONG_BLOB: 'TextField',
#     FIELD_TYPE_NUM.VAR_STRING: 'CharField',
# }