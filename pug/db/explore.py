from traceback import print_exc
from collections import OrderedDict, Mapping
from decimal import Decimal

import re
import json
from dateutil import parser

from ..nlp import db
from ..nlp import sqlserver as sql

from django.core.exceptions import ImproperlyConfigured
try:
    from django.db import models, connection, connections
except ImproperlyConfigured:
    import traceback
    print traceback.format_exc()
    print 'WARNING: The module named %r from file %r' % (__name__, __file__)
    print '         can only be used within a Django project!'
    print '         Though the module was imported, some of its functions may raise exceptions.'


types_not_countable = ('text',)
types_not_aggregatable = ('text', 'bit',)


def clean_utf8(utf8_string):
    r"""Delete any invalid symbols in a UTF-8 encoded string

    Returns the cleaned string.
    
    >>> clean_utf8('A\xffB\xffC ')
    'ABC '
    """
    if isinstance(utf8_string, basestring):
        while True:
            try:
                json.dumps(utf8_string)
                break
            except UnicodeDecodeError as e:
                m = re.match(r".*can't[ ]decode[ ]byte[ ]0x[0-9a-fA-F]{2}[ ]in[ ]position[ ](\d+)[ :.].*", str(e))
                if m and m.group(1):
                    i = int(m.group(1))
                    utf8_string = utf8_string[:i] + utf8_string[i+1:]
                else:
                    raise e
    return utf8_string


def get_cursor_table_names(cursor):
    return [row[-2] for row in cursor.execute("""SELECT * FROM information_schema.tables""").fetchall()]


def inspect_cursor(cursor=None):
    if isinstance(cursor, basestring):
        cursor = connections[cursor].cursor()
    if not cursor:
        cursor = connections['default']
    for table_name in get_cursor_table_names(cursor):
        print table_name

# FIXME: break `inspect_db` into modules that make sense, like:
#   inspect_column()
#   inspect_table()
#   count_values()
#   count_unique()
def inspect_db(app='refurb', db_alias='refurb', table=None, verbosity=2, column=None):
    if app and isinstance(app, basestring):
        app = db.get_app(app)
    model_names = list(mc.__name__ for mc in models.get_models(app))
    meta = OrderedDict()
    for model_name in model_names:
        model = db.get_model(model_name, app=app)
        if table is not None and isinstance(table, basestring):
            if model._meta.db_table != table:
                if verbosity>1:
                    print 'skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        elif callable(table):
            if not table(model._meta.db_table):
                if verbosity>1:
                    print 'skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        meta[model_name] = OrderedDict()
        meta[model_name]['Meta'] = OrderedDict()
        meta[model_name]['Meta']['primary_key'] = None
        meta[model_name]['Meta']['count'] = model.objects.using(db_alias).count()
        meta[model_name]['Meta']['db_table'] = model._meta.db_table
        
        if verbosity>1:
            print '%s.Meta = %r' % (model_name, meta[model_name]['Meta'])
        
        # meta[model_name]['Meta']['db_name'] = db_alias
        properties_of_fields = sql.get_meta_dicts(cursor=db_alias, table=meta[model_name]['Meta']['db_table'])
        field_properties_dict = OrderedDict((field['name'], field) for field in properties_of_fields)
        if verbosity > 1:
            print '-' * 20 + model_name + '-' * 20
        db_primary_keys = [field['name'] for field in properties_of_fields if field['primary_key']]
        if len(db_primary_keys) == 1:
            meta[model_name]['Meta']['primary_key'] = db_primary_keys[0]
        for field in model._meta._fields():
            db_column = field.db_column
            if not db_column:
                if field.name in field_properties_dict:
                    db_column = field.name
                elif field.name.lower() in field_properties_dict:
                    db_column = field.name.lower()
                elif field.name.upper() in field_properties_dict:
                    db_column = field.name.upper()
            if not db_column:
                if verbosity > 1:
                    print "WARNING: Skipped field named '%s'. No column found in the database.table '%s.%s'." % (field.name, db_alias, meta[model_name]['Meta']['db_table'])
                continue
            if column is not None and isinstance(column, basestring):
                if db_column != column:
                    if verbosity>1:
                        print 'Skipped field named %s.%s with db column name %s.%s.' % (model_name, field.name, model._meta.db_table, db_column)
                    continue
            elif callable(column):
                if not column(db_column):
                    if verbosity>1:
                        print 'Skipped field named %s.%s with db column name %s.%s.' % (model_name, field.name, model._meta.db_table, db_column)
                    continue
            if (field.name == 'id' and isinstance(field, models.fields.AutoField)
                    and field.primary_key and (not field_properties_dict[db_column]['primary_key'])):
                continue

            # Calculate the fraction of values in a column that are distinct (unique).
            #   For columns that aren't populated with 100% distinct values, the fraction may help identify columns that are part of a  "unique-together" compound key
            #   Necessary constraint for col1 and col2 to be compound key: col1_uniqueness + col2_uniqueness >= 1.0 (100%)
            # TODO: check for other clues about primary_keyness besides just uniqueness 
            field_properties_dict[db_column]['num_distinct'] = None
            field_properties_dict[db_column]['num_null'] = None
            if field_properties_dict[db_column]['type'] not in types_not_countable:
                field_properties_dict[db_column]['num_distinct'] = model.objects.using(db_alias).values(field.name).distinct().count()
                field_properties_dict[db_column]['num_null'] = model.objects.using(db_alias).filter(**{'%s__isnull' % field.name: True}).count()

            field_properties_dict[db_column]['max'] = None
            field_properties_dict[db_column]['min'] = None
            # check field_properties_dict[db_column]['num_null'] for all Null first?
            if field_properties_dict[db_column]['type'] not in types_not_aggregatable:
                connection.close()
                try:
                    field_properties_dict[db_column]['max'] = clean_utf8(model.objects.using(db_alias).aggregate(max_value=models.Max(field.name))['max_value'])
                    field_properties_dict[db_column]['min'] = clean_utf8(model.objects.using(db_alias).aggregate(min_value=models.Min(field.name))['min_value'])
                except ValueError, e:
                    if verbosity > 1:
                        print_exc()
                        print "ValueError (UnicodeDecodeError?): Skipped max/min calculations for field named '%s' (%s) because of %s." % (field.name, repr(db_column), e)
                    connection.close()
                # validate values that might be invalid strings do to db encoding/decoding errors (make sure they are UTF-8
                for k in ('min', 'max'):
                    clean_utf8(field_properties_dict.get(db_column, {}).get(k))



            # field_properties_dict[db_column]['count'] = N
            if verbosity > 2:
                print '%s (%s) has %s / %s (%3.1f%%) distinct values between %s and %s, excluding %s nulls.' % (field.name, db_column, 
                                                             field_properties_dict[db_column]['num_distinct'], 
                                                             meta[model_name]['Meta']['count'],
                                                             100. * (field_properties_dict[db_column]['num_distinct'] or 0) / (meta[model_name]['Meta']['count'] or 1),
                                                             repr(field_properties_dict[db_column]['min']),
                                                             repr(field_properties_dict[db_column]['max']),
                                                             field_properties_dict[db_column]['num_null'])
            # TODO:
            #   1. count the number of values that are strings that could be converted to
            #      a. integers
            #      b. floats
            #      c. dates / datetimes
            #      d. booleans / nullbooleans
            #      e. other ordinal, categorical, or quantitative types
            #   2. count the number of null values
            #      a. null/None
            #      b. blank
            #      c. whitespace or other strings signifying null ('NULL', 'None', 'N/A', 'NaN', 'Not provided')
        if verbosity > 1:
            print field_properties_dict 
        meta[model_name].update(field_properties_dict)
    return meta


def get_indexes(meta, table_name=None, model_name=None):
    """Find all the indexes (primary keys) based on the meta data 
    """
    indexes, pk_field = {}, None

    indexes = []
    for meta_model_name, model_meta in meta.iteritems():
        if (table_name or model_name) and not (table_name == model_meta['Meta'].get('db_table', '') or model_name == meta_model_name):
            continue
        field_name, field_infodict, score = get_index(model_meta)
        indexes.append(('%s.%s' % (meta_model_name, field_name), field_infodict, score))
    return indexes


def try_convert(value, datetime_to_ms=False, precise=False):
    """Convert a str into more useful python type (datetime, float, int, bool), if possible

    Some precision may be lost (e.g. Decimal converted to a float)

    >>> try_convert('false')
    False
    >>> try_convert('123456789.123456789')
    123456789.123456
    >>> try_convert('1234')
    1234
    >>> try_convert(1234)
    1234
    >>> try_convert(['1234'])
    ['1234']
    >>> try_convert('12345678901234567890123456789012345678901234567890', precise=True)
    12345678901234567890123456789012345678901234567890L
    >>> try_convert('12345678901234567890123456789012345678901234567890.1', precise=True)
    Decimal('12345678901234567890123456789012345678901234567890.1')
    """
    if not isinstance(value, basestring):
        return value
    try:
        dt = parser.parse(value)
        if datetime_to_ms:
            return db.datetime_in_milliseconds(dt)
        return dt
    except:
        if not precise:
            try:
                return int(value)
            except:
                try:
                    return float(value)
                except:
                    pass
        else:
            dec, i, f = None, None, None
            try:
                dec = Decimal(value)
            except:
                return try_convert(value, precise=False)
            try:
                i = int(value)
            except:
                try:
                    f = float(value)
                except:
                    pass
            if dec is not None:
                if dec == i:
                    return i
                elif dec == f:
                    return f
                return dec

    if value in db.YES_VALUES or value in db.TRUE_VALUES:
        return True
    elif value in db.NO_VALUES or value in db.FALSE_VALUES:
        return False
    elif value in db.NULL_VALUES:
        return None
    return value


def convert_loaded_json(js):
    """Convert strings loaded as part of a json file/string to native python types

    convert_loaded_json({'x': '123'})
    {'x': 123}
    convert_loaded_json([{'x': '123.'}, {'x': 'Jan 28, 2014'}])
    [{'x': 123}, datetime.datetime(2014, 1, 18)]
    """
    if not isinstance(js, (Mapping, tuple, list)):
        return try_convert(js)
    try:
        return type(js)(convert_loaded_json(item) for item in js.iteritems())
    except:
        try:
            return type(js)(convert_loaded_json(item) for item in iter(js))
        except:
            return try_convert(js)


def get_index(model_meta, weights=None):
    """Return a single (field_name, infodict pair) for the model metadata dict provided

    return value format is: 
        ( 
            field_name, {
                'primary_key': boolean representing whether it's the primary key,
                'unique': boolean representing whether it's a unique index 
            }
        )
    """
    weights = weights or get_index.default_weights
    N = model_meta['Meta'].get('count', 0)
    for field_name, field_meta in model_meta.iteritems():
        if field_name == 'Meta':
            continue
        pkfield = field_meta.get('primary_key')
        if pkfield:
            print pkfield
            # TODO: Allow more than one index per model/table
            return {
                field_name: {
                    'primary_key': True,
                    'unique': field_meta.get('unique') or (
                        N >= 3 and field_meta.get('num_null') <= 1
                        and field_meta.get('num_distinct') == N),
                    }}
    score_names = []
    for field_name, field_meta in model_meta.iteritems():
        score = 0
        for feature, weight in weights:
            # for categorical features (strings), need to look for a particular value
            value = field_meta.get(feature)
            if isinstance(weight, tuple):
                if value is not None and value in (float, int):
                    score += weight * value
                if callable(weight[1]):
                    score += weight[0] * weight[1](field_meta.get(feature))
                else:
                    score += weight[0] * (field_meta.get(feature) == weight[1])
            else:
                feature_value = field_meta.get(feature)
                if feature_value is not None:
                    score += weight * field_meta.get(feature)
        score_names += [(score, field_name)]
    max_name = max(score_names)
    field_meta = model_meta[max_name[1]]
    return (
        max_name[1],
        {
            'primary_key': True,
            'unique': field_meta.get('unique') or (
                N >= 3 
                and field_meta.get('num_null') <= 1 
                and field_meta.get('num_distinct') == N),
        },
        max_name[0],
        )
get_index.default_weights = (('num_distinct', (1e-3, 'normalize')), ('unique', 1.), ('num_null', (-1e-3, 'normalize')), ('fraction_null', -2.), 
                             ('type', (.3, 'numeric')), ('type', (.2, 'char')), ('type',(-.3, 'text')),
                            )

                    
def models_with_unique_column(meta, exclude_single_pk=True, exclude_multi_pk=True):
    """Return a list of model names for models that have at least 1 field that has all distinct values (could be used as primary_key)"""
    models_with_potential_pk = []
    for model_name, model_fields in meta.iteritems():
        if exclude_single_pk:
            if model_fields['Meta']['primary_key']:
                continue
        if exclude_multi_pk:
            if any(not field['primary_key'] and field['num_distinct'] == 1 for field in model_fields if field is not 'Meta'):
                models_with_potential_pk += model_name
        else:
            if any(field['num_distinct'] == 1 for field in model_fields if field is not 'Meta'):
                models_with_potential_pk += model_name
    return models_with_potential_pk