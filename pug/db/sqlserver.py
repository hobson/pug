from django.db import connections  #, transaction
from collections import OrderedDict, namedtuple
from django.conf import settings


def dicts_from_table(table, keys=None):
    lod = []
    for row in table:
        if not keys:
            keys = row
            if not all((k not in (None, '') or bool(k.strip())) for k in keys):
                keys = None
            continue
        lod += [OrderedDict((k, v) for k, v in zip(keys, row))]
    return lod


def namedtuples_from_table(table, keys=None):
    lont = []
    for row in table:
        if not keys:
            keys = row
            if not all((k not in (None, '') or bool(k.strip())) for k in keys):
                keys = None
            NamedTuple = namedtuple('NamedTuple', ' '.join([k.strip() for k in keys]))
            #print keys
            #print NamedTuple
            continue
        lont += [NamedTuple(*row)]
    #print lont
    return lont

# FIXME: this gives a much different answer than django ORM queries used in inspectdb
def column_properties_sql(table_name):
    """SQL query string for retrieving column names and properties for a sqlserver db table 

    from marc_s at http://stackoverflow.com/a/2418665/623735"""

    sql = """
    SELECT 
        c.name 'Column Name',
        t.Name 'Data type',
        c.max_length 'Max Length',
        c.precision ,
        c.scale ,
        c.is_nullable,
        ISNULL(i.is_primary_key, 0) 'Primary Key'
    FROM    
        sys.columns c
    INNER JOIN 
        sys.types t ON c.system_type_id = t.system_type_id
    LEFT OUTER JOIN 
        sys.index_columns ic ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    LEFT OUTER JOIN 
        sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    WHERE
        c.object_id = OBJECT_ID('""" + str(table_name) + "')"
    #print sql
    return sql


def make_cursor(cursor='default'):
    # a connection might need to be converted to a cursor, cursors have a noncallable attribute "cursor" so watch out
    if hasattr(cursor, 'cursor') and callable(cursor.cursor):
        cursor = cursor.cursor()
    # a db_alias might need to be converted to a cursor
    elif isinstance(cursor, basestring) and cursor in settings.DATABASES:
        cursor = connections[cursor].cursor()
    return cursor


def datatype(dbtype, description, cursor):
    """Google AppEngine Helper to convert a data type into a string."""
    dt = cursor.db.introspection.get_field_type(dbtype, description)
    if type(dt) is tuple:
        return dt[0]
    else:
        return dt


def get_meta_table(cursor='default', table=None):
    cursor = make_cursor(cursor)

    # from dev branch of Django
    # FieldInfo = namedtuple('FieldInfo','name type_code display_size internal_size precision scale null_ok')
    ans = [('name', 'type', 'display_size', 'internal_size', 'precision', 'scale', 'null_ok', 'primary_key')]

    #pep249 http://www.python.org/dev/peps/pep-0249
    #0: name  (mandatory)
    #1: type_code  (mandatory)
    #2: display_size  (optional/nullable)
    #3: internal_size  (optional/nullable)
    #4: precision  (optional/nullable)
    #5: scale  (optional/nullable)
    #6: null_ok  (optional/nullable)

    #pep249 implementation by psycopg.cursor.description
    #0: name: the name of the column returned.
    #1: type_code: the PostgreSQL OID of the column. You can use the pg_type system table to get more informations about the type. This is the value used by Psycopg to decide what Python type use to represent the value. See also Type casting of SQL types into Python objects.
    #2: display_size: the actual length of the column in bytes. Obtaining this value is computationally intensive, so it is always None unless the PSYCOPG_DISPLAY_SIZE parameter is set at compile time. See also PQgetlength.
    #3: internal_size: the size in bytes of the column associated to this column on the server. Set to a negative value for variable-size types See also PQfsize.
    #4: precision: total number of significant digits in columns of type NUMERIC. None for other types.
    #5: scale: count of decimal digits in the fractional part in columns of type NUMERIC. None for other types.
    #6: null_ok: always None as not easy to retrieve from the libpq.
    
    #pyodbc.cursor.columns implementation:
    #0: table_cat
    #1: table_schem
    #2: table_name
    #3: column_name
    #4: data_type
    #5: type_name
    #6: column_size
    #7: buffer_length
    #8: decimal_digits
    #9: num_prec_radix
    #10: nullable
    #11: remarks
    #12: column_def
    #13: sql_data_type
    #14: sql_datetime_sub
    #15: char_octet_length
    #16: ordinal_position
    #17: is_nullable: One of SQL_NULLABLE, SQL_NO_NULLS, SQL_NULLS_UNKNOWN.

    #augmented pep249 provided here(TBD)
    #7: primary_key (True if the column value is used as an index or primary key)
    #8: num_distinct (number of distinct values)
    #9: num_null (number of null values)
    #10: max_value
    #11: min_value

    # # custom microsoft SQL query of metadata (works poorly in comparison to others)
    # if cursor.cursor.__class__.__module__.endswith('odbc.base'):
    #     ans += [[c[0], c[1], c[2], c[2], c[3], c[4], c[5], c[6]] for c in cursor.execute(column_properties_sql(table)).fetchall()]
    # # pyodbc
    # elif hasattr(cursor, 'columns') and callable(cursor.columns):
    #     ans += [[c[3], c[4], None, c[6], c[6], c[8], c[10]] for c in cursor.columns(table=table)]
    # # psycopg
    # else:
    meta_table = cursor.db.introspection.get_table_description(cursor, table)
    ans += [list(c) + [None] for c in meta_table]
    return ans

DATATYPE_TO_FIELDTYPE = {'int': 'IntegerField', 'float': 'FloatField', 'text': 'TextField', 'char': 'CharField', 'Decimal': 'DecimalField'}
def datatype_to_fieldtype(datatype):
    return DATATYPE_TO_FIELDTYPE.get(datatype, 'TextField')

def get_meta_tuples(cursor='default', table=None):
    return namedtuples_from_table(get_meta_table(cursor=cursor, table=table))

def get_meta_dicts(cursor='default', table=None):
    return dicts_from_table(get_meta_table(cursor=cursor, table=table))

def primary_keys(cursor='default', table=None):
    list_of_fields = get_meta_tuples(cursor=cursor, table=table)
    return [field.name for field in list_of_fields if field['primary_key']]