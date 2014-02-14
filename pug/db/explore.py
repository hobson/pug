from traceback import print_exc
from collections import OrderedDict, Mapping
from decimal import Decimal
import sqlparse
import re
import json

from dateutil import parser
import datetime

from pug.nlp import djdb  # FIXME: confusing name (too similar to common `import as` for django.db)
from pug.nlp import db
import sqlserver as sql


from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError

DEFAULT_DB_ALIAS = 'default'
DEFAULT_APP_NAME = None
try:
    from django.db import models, connection, connections, router
    from django.conf import settings
    DEFAULT_APP_NAME = settings.INSTALLED_APPS[-1].split('.')[-1]
except ImproperlyConfigured:
    import traceback
    print traceback.format_exc()
    print 'WARNING: The module named %r from file %r' % (__name__, __file__)
    print '         can only be used within a Django project!'
    print '         Though the module was imported, some of its functions may raise exceptions.'

types_not_countable = ('text',)
types_not_aggregatable = ('text', 'bit',)


def get_db_meta(app=DEFAULT_APP_NAME, db_alias=None, table=None, verbosity=0, column=None):
    """Return a dict of dicts containing metadata about the database tables associated with an app

    TODO: allow multiple apps
    >>> get_db_meta('crawler', db_alias='default', table='crawler_wikiitem')  # doctest: +ELLIPSIS
    OrderedDict([('WikiItem', OrderedDict([('Meta', OrderedDict([('primary_key', None), ('count', 1332), ('db_table', u'crawler_wikiitem')])), ('id', OrderedDict([('name', 'id'), ('type', ...
    """
    if app and isinstance(app, basestring):
        app = djdb.get_app(app)
    else:
        app = djdb.get_app('')
    model_names = list(mc.__name__ for mc in models.get_models(app))
    meta = OrderedDict()
    # inspectdb uses: for table_name in connection.introspection.table_names(cursor):
    for model_name in model_names:
        model = djdb.get_model(model_name, app=app)
        if db_alias:
            model_db_alias = db_alias
        else:
            model_db_alias = router.db_for_read(model)
        queryset = model.objects
        if model_db_alias:
            queryset = queryset.using(model_db_alias)
        if model and table is not None and isinstance(table, basestring):
            if model._meta.db_table != table:
                if verbosity>1:
                    print 'skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        elif callable(table):
            if not table(model._meta.db_table):
                if verbosity>1:
                    print 'skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        count = None
        try:
            print 'trying to count for model %r and db_alias %r' % (model, model_db_alias)
            count = queryset.count()
        except DatabaseError, e:
            if verbosity:
                print_exc()
                print "DatabaseError: Unable to count records for model '%s' (%s) because of %s." % (model.__name__, repr(model), e)
            connection.close()
        except:
            print_exc()
            print 'Connection doesnt exist?'

        meta[model_name] = OrderedDict()
        meta[model_name]['Meta'] = OrderedDict()
        meta[model_name]['Meta']['primary_key'] = None
        meta[model_name]['Meta']['count'] = count
        meta[model_name]['Meta']['db_table'] = model._meta.db_table
        
        if verbosity > 1:
            print '%s.Meta = %r' % (model_name, meta[model_name]['Meta'])
        
        # inspectdb uses: connection.introspection.get_table_description(cursor, table_name)
        properties_of_fields = sql.get_meta_dicts(cursor=model_db_alias, table=meta[model_name]['Meta']['db_table'], verbosity=verbosity)
        model_meta = OrderedDict((field['name'], field) for field in properties_of_fields)
        if verbosity > 1:
            print '-' * 20 + model_name + '-' * 20
        db_primary_keys = [field['name'] for field in properties_of_fields if field['primary_key']]
        if len(db_primary_keys) == 1:
            meta[model_name]['Meta']['primary_key'] = db_primary_keys[0]

        # augment model_meta with additional stats, but only if there are enough rows to get statistics
        model_meta = augment_model_meta(model, model_db_alias, model_meta, column_name_filter=column, count=count, verbosity=verbosity)

        if verbosity > 1:
            print model_meta
        meta[model_name].update(model_meta)
    return meta


def augment_model_meta(model, db_alias, model_meta, column_name_filter=None, count=0, verbosity=0):
    """Fields are keyed by their db_column name rather than field name (like model_meta)"""
    queryset = model.objects
    if db_alias:
        queryset = queryset.using(db_alias)
    for field in model._meta._fields():
        db_column = field.db_column
        if not db_column:
            if field.name in model_meta:
                db_column = field.name
            elif field.name.lower() in model_meta:
                db_column = field.name.lower()
            elif field.name.upper() in model_meta:
                db_column = field.name.upper()
        if not db_column:
            if verbosity:
                print "WARNING: Skipped field named '%s'. No column found in the database.table '%s.%s'." % (field.name, db_alias, model.__name__)
            continue
        if column_name_filter is not None and isinstance(column_name_filter, basestring):
            if db_column != column_name_filter:
                # if verbosity>1:
                #     print 'Skipped field named %s.%s with db column name %s.%s.' % (model_name, field.name, model._meta.db_table, db_column)
                continue
        elif callable(column_name_filter):
            if not column_name_filter(db_column):
                # if verbosity>1:
                #     print 'Skipped field named %s.%s with db column name %s.%s.' % (model_name, field.name, model._meta.db_table, db_column)
                continue
        if (field.name == 'id' and isinstance(field, models.fields.AutoField)
                and field.primary_key and (not model_meta[db_column]['primary_key'])):
            continue

        model_meta[db_column] = augment_field_meta(field, queryset, model_meta[db_column], count=count)
        if verbosity > 2:
            print '%s (%s) has %s / %s (%3.1f%%) distinct values between %s and %s, excluding %s nulls.' % (field.name, db_column, 
                                                         model_meta[db_column]['num_distinct'], 
                                                         count,
                                                         100. * (model_meta[db_column]['num_distinct'] or 0) / (count or 1),
                                                         repr(model_meta[db_column]['min']),
                                                         repr(model_meta[db_column]['max']),
                                                         model_meta[db_column]['num_null'])
    return model_meta


def augment_field_meta(field, queryset, field_properties, verbosity=0, count=0):
    """Return a dict of statistical properties (metadata) for a database column (model field)

    Strings are UTF-8 encoded
    Resulting dictionary is json-serializable using the pug.nlp.db.RobustEncoder class.

    {
        'num_distinct':   # count of distinct (different) discrete values within the column
        'min':   # minimum value
        'max':   # maximum value
        'num_null':   # count of the Null or None values in the column
        'type':  # database column type
    }

    TODO:
      1. count the number of values that are strings that could be converted to
         a. integers
         b. floats
         c. dates / datetimes
         d. booleans / nullbooleans
         e. other ordinal, categorical, or quantitative types
      2. count the number of null values
         a. null/None
         b. blank
         c. whitespace or other strings signifying null ('NULL', 'None', 'N/A', 'NaN', 'Not provided')
    """
    # Calculate the fraction of values in a column that are distinct (unique).
    #   For columns that aren't populated with 100% distinct values, the fraction may help identify columns that are part of a  "unique-together" compound key
    #   Necessary constraint for col1 and col2 to be compound key: col1_uniqueness + col2_uniqueness >= 1.0 (100%)
    # TODO: check for other clues about primary_keyness besides just uniqueness 
    field_properties['num_distinct'] = count
    field_properties['num_null'] = count
    field_properties['fraction_distinct'] = count
    typ = field_properties.get('type')
    if typ and typ not in types_not_countable and count:
        field_properties['num_distinct'] = queryset.values(field.name).distinct().count()
        field_properties['num_null'] = queryset.filter(**{'%s__isnull' % field.name: True}).count()
        field_properties['fraction_distinct'] = float(field_properties['num_distinct']) / (queryset.count() or 1)

    field_properties['max'] = None
    field_properties['min'] = None
    # check field_properties['num_null'] for all Null first?
    if count and typ and typ not in types_not_aggregatable:
        connection.close()
        try:
            field_properties['max'] = clean_utf8(queryset.aggregate(max_value=models.Max(field.name))['max_value'])
            field_properties['min'] = clean_utf8(queryset.aggregate(min_value=models.Min(field.name))['min_value'])
        except ValueError, e:
            if verbosity:
                print_exc()
                print "ValueError (perhaps UnicodeDecodeError?): Skipped max/min calculations for field named '%s' (%s) because of %s." % (field.name, repr(field.db_column), e)
            connection.close()
        except DatabaseError, e:
            if verbosity:
                print_exc()
                print "DatabaseError: Skipped max/min calculations for field named '%s' (%s) because of %s." % (field.name, repr(field.db_column), e)
            connection.close()
        # validate values that might be invalid strings do to db encoding/decoding errors (make sure they are UTF-8
        for k in ('min', 'max'):
            clean_utf8(field_properties.get(k))

    return field_properties

def get_index(model_meta, weights=None, verbosity=0):
    """Return a single tuple of index metadata for the model metadata dict provided

    return value format is: 

        ( 
            field_name,
            {
                'primary_key': boolean representing whether it's the primary key,
                'unique': boolean representing whether it's a unique index 
            },
            score,
        )
    """
    weights = weights or get_index.default_weights
    N = model_meta['Meta'].get('count', 0)
    for field_name, field_meta in model_meta.iteritems():
        if field_name == 'Meta':
            continue
        pkfield = field_meta.get('primary_key')
        if pkfield:
            if verbosity > 1:
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


def meta_to_indexes(meta, table_name=None, model_name=None):
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


def get_relations(cursor, table_name, app=DEFAULT_APP_NAME, db_alias=None):
    #meta = get_db_meta(app=app, db_alias=db_alias, table=table_name, verbosity=0)
    return {}

def get_indexes(cursor, table_name, app=DEFAULT_APP_NAME, db_alias=None, verbosity=0):
    meta = get_db_meta(app=app, db_alias=db_alias, table=table_name, verbosity=0)
    if verbosity > 1:
        print meta
    return {}

def try_convert(value, datetime_to_ms=False, precise=False):
    """Convert a str into more useful python type (datetime, float, int, bool), if possible

    Some precision may be lost (e.g. Decimal converted to a float)

    >>> try_convert('false')
    False
    >>> try_convert('123456789.123456')
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
    if value in db.YES_VALUES or value in db.TRUE_VALUES:
        return True
    elif value in db.NO_VALUES or value in db.FALSE_VALUES:
        return False
    elif value in db.NULL_VALUES:
        return None
    try:
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
    except:
        pass
    try:
        dt = parser.parse(value)
        if dt and isinstance(dt, datetime.datetime) and (3000 >= dt.year >= 1900):
            if datetime_to_ms:
                return db.datetime_in_milliseconds(dt)
            return dt
    except:
        pass
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

                    
def models_with_unique_column(meta, exclude_single_pk=True, exclude_multi_pk=True):
    """Return a list of model names for models that have at least 1 field that has all distinct values (could be used as primary_key)"""
    models_with_potential_pk = {}
    fields_distinct = {}
    for model_name, model_fields in meta.iteritems():
        if exclude_single_pk and model_fields['Meta']['primary_key']:
                continue
        fields_distinct = []
        for field_name, field in model_fields.iteritems():
            if field_name is 'Meta':
                continue
            if float(field.get('fraction_distinct', 0)) == 1.:
                fields_distinct += [field_name]
        # if any(not field['primary_key'] and field['num_distinct'] == 1 for field_name, field in model_fields.iteritems() if field is not 'Meta'):
        if (not exclude_multi_pk and fields_distinct) or len(fields_distinct) == 1:
            models_with_potential_pk[model_name] = fields_distinct
    return models_with_potential_pk


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

def print_cursor_table_names(cursor=None):
    if isinstance(cursor, basestring):
        cursor = connections[cursor].cursor()
    if not cursor:
        cursor = connections['default']
    for table_name in get_cursor_table_names(cursor):
        print table_name


class QueryTimer(object):
    """Based on https://github.com/jfalkner/Efficient-Django-QuerySet-Use

    >>> from example.models import Sample
    >>> qt = QueryTimer()
    >>> cm_list = list(Sample.objects.values()[:10])
    >>> qt.stop()  # doctest: +ELLIPSIS
    QueryTimer(time=0.0..., num_queries=1)
    """

    def __init__(self, time=None, num_queries=None, sql=None, conn=None):
        if isinstance(conn, basestring):
            conn = connections[conn]
        self.conn = conn or connection
        self.time, self.num_queries = time, num_queries
        self.start_time, self.start_queries, self.queries = None, None, None
        self.sql = sql or []
        self.start()

    def start(self):
        self.queries = []
        self.start_time = datetime.datetime.now()
        self.start_queries = len(self.conn.queries)

    def stop(self):
        self.time = (datetime.datetime.now() - self.start_time).total_seconds()
        self.queries = self.conn.queries[self.start_queries:]
        self.num_queries = len(self.queries)
        print self

    def format_sql(self):
        if self.time is None or self.queries is None:
            self.stop()
        if self.queries or not self.sql:
            self.sql = []
            for query in self.queries:
                self.sql += [sqlparse.format(query['sql'], reindent=True, keyword_case='upper')]
        return self.sql

    def __repr__(self):
        return '%s(time=%s, num_queries=%s)' % (self.__class__.__name__, self.time, self.num_queries)
