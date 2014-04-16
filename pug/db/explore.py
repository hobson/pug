from traceback import print_exc
from collections import OrderedDict, Mapping
from decimal import Decimal
import sqlparse
import re
import json
import chardet
import datetime

import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser
from progressbar import ProgressBar, Bar, Percentage, ETA, RotatingMarker

from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.core.exceptions import FieldError
from django.db.models import FieldDoesNotExist

from pug.nlp import djdb  # FIXME: confusing name (too similar to common `import as` for django.db)
from pug.nlp import db
#from pug.nlp import util
import sqlserver as sql


DEFAULT_DB_ALIAS = None  # 'default'
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

types_varchar = ['nvarchar', 'varchar', 'sysname']  # `sysname` stores MS-TSQL object names and is equivalent to `nvarchar(128)`
types_not_countable = ['text', 'image', 'ntext']
types_not_aggregatable = types_not_countable + ['bit', 'uniqueidentifier']


def get_app_meta(apps=None, app_filter=lambda x: x.startswith('sec_') or x.startswith('siica_'), app_exclude_filter=None, verbosity=0, save=True):
    apps = apps or djdb.get_app(apps)
    meta = []
    for app in apps:
        if filter_reject(app, app_filter, app_exclude_filter):
            continue
        meta += [get_db_meta(app=app, verbosity=verbosity)]
        if save:
            try:
                with open('db_meta_%s.json' % app, 'w') as fpout:
                    json.dump(make_serializable(meta[-1]), fpout, indent=4)
            except:
                print_exc()
    if save:
        try:
            with open('db_meta_all_apps.json', 'w') as fpout:
                jsonifiable_data = make_serializable(meta)
                json.dump(jsonifiable_data, fpout, indent=4)
        except:
            print_exc()
    return meta


def filter_reject(s, accept_filters, reject_filters=None):
    if callable(accept_filters) and callable(reject_filters):
        if (accept_filters and not accept_filters(s)) and (not reject_filters or not reject_filters(s)):
            return True
        else:
            return False
    elif isinstance(accept_filters, (tuple, list, set)) and (not reject_filters or callable(reject_filters)):
        return any(filter_reject(s, af, reject_filters) for af in accept_filters)
    elif (not accept_filters or callable(accept_filters)) and isinstance(reject_filters, (tuple, list, set)):
        return any(filter_reject(s, accept_filters, rf) for rf in reject_filters)
    elif (not reject_filters or callable(reject_filters)) and isinstance(accept_filters, (tuple, list, set)):
        return any(filter_reject(s, af, reject_filters) for af in accept_filters)
    elif isinstance(accept_filters, basestring) and (not reject_filters or callable(reject_filters)):
        return filter_reject(s, lambda x: x.startswith(accept_filters), reject_filters)
    elif (not accept_filters or callable(accept_filters)) and isinstance(reject_filters, basestring):
        return filter_reject(s, accept_filters, lambda x: x.startswith(reject_filters))

    return None


def load_app_meta(apps=None, app_filter=['sec_', 'siica_'], app_exclude_filter=None):
    apps = apps or djdb.get_app(apps)
    meta = {}
    for app in apps:
        # if filter_reject(app, app_filter, app_exclude_filter):
        #     continue
        if (app_filter and not any(app.startswith(af) for af in app_filter)) and (
                not app_exclude_filter or not any(app.startswith(rf) for rf in app_exclude_filter)):
            continue
        with open('db_meta_%s.json' % app, 'r') as fpin:        
            m = json.load(fpin)
        for table_name, table_meta in m.iteritems():
            table_name = app + '.' + table_name
            for field_name, field_meta in table_meta.iteritems():
                meta[table_name + '.' + field_name] = field_meta
    return meta


def meta_bar_chart(series=None, N=20):
    "Each column in the series is a dict of dicts"
    if not series or isinstance(series, basestring):
        series = json.load(load_app_meta)
    if isinstance(series, Mapping) and isinstance(series.values()[0], Mapping):
        rows_received = series['# Received'].items()
    elif isinstance(series, Mapping):
        rows_received = series.items()
    else:
        rows_received = list(series)

    #rows = sorted(rows, key=operator.itemgetter(1), reverse=True)
    rows = sorted(rows_received, key=lambda x: x[1], reverse=True)
    received_names, received_qty = zip(*rows)
    ra_qty = [(series['Qty in RA'].get(name, 0.) or 0.) for name in received_names]
    # percent = [100. - 100. * (num or 0.) / (den or 1.) for num, den in zip(received_qty, ra_qty)]

    # only care about the top 30 model numbers in terms of quantity
    #ind = range(N)

    figs = []

    figs += [plt.figure()]
    ax = figs[-1].add_subplot(111)
    ax.set_ylabel('# Units Returned')
    ax.set_title('Most-Returned LCDTV Models 2013-present')
    x = np.arange(N)
    bars1 = ax.bar(x, received_qty[:N], color='b', width=.4, log=1)
    bars2 = ax.bar(x+.4, ra_qty[:N], color='g', width=.4, log=1)
    ax.set_xticks(range(N))
    ax.set_xticklabels(received_names[:N], rotation=35)
    ax.grid(True)
    ax.legend((bars1[0], bars2[0]), ('# in RA', '# Received'), 'center right')
    figs[-1].show()
    #fig.autofmt_xdate()


def get_db_meta(app=DEFAULT_APP_NAME, db_alias=None, table=None, verbosity=0, column=None):
    """Return a dict of dicts containing metadata about the database tables associated with an app

    TODO: allow multiple apps
    >>> get_db_meta('crawler', db_alias='default', table='crawler_wikiitem')  # doctest: +ELLIPSIS
    OrderedDict([('WikiItem', OrderedDict([('Meta', OrderedDict([('primary_key', None), ('count', 1332), ('db_table', u'crawler_wikiitem')])), (u'id', OrderedDict([('name', u'id'), ('type', ...
    """
    if verbosity:
        print 'Looking for app %r.' % (app, )
    if app and isinstance(app, basestring):
        app = djdb.get_app(app, verbosity=verbosity)
    else:
        app = djdb.get_app('')
    model_names = list(mc.__name__ for mc in models.get_models(app))
    if verbosity:
        print 'Found %d models for app %r.' % (len(model_names), app)
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
                    print 'Skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        elif callable(table):
            if not table(model._meta.db_table):
                if verbosity>1:
                    print 'Skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        count = None
        try:
            if verbosity > 1:
                print 'Trying to count records in model %r and db_alias %r' % (model, model_db_alias)
            count = queryset.count()
        except DatabaseError as e:
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
    for field_name in model._meta.get_all_field_names():
        field = None
        try:
            field = model._meta.get_field(field_name)
            db_column = field.db_column
        # Django creates reverse ForeignKey relationship fields that may not have a database column in this table
        # This happens if you make existing fields/columns in other tables a ForeignKey referencing this table
        except FieldDoesNotExist:
            db_column = None
        if not field:
            if verbosity:
                print "WARNING: Skipped 'phantom' field named '%s'. No field found in the model '%s' for database '%s'." % (field_name, model.__name__, db_alias)
            continue
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

        model_meta[db_column] = augment_field_meta(field, queryset, model_meta[db_column], count=count, verbosity=verbosity)
        if verbosity > 2:
            print '%s (%s of type %s) has %s / %s (%3.1f%%) distinct values between %s and %s, excluding %s nulls.' % (field.name, db_column, 
                                                        model_meta[db_column]['type'],
                                                        model_meta[db_column]['num_distinct'], 
                                                        count,
                                                        100. * (model_meta[db_column]['num_distinct'] or 0) / (count or 1),
                                                        repr(model_meta[db_column]['min']),
                                                        repr(model_meta[db_column]['max']),
                                                        model_meta[db_column]['num_null'])
    return model_meta


def augment_field_meta(field, queryset, field_properties, verbosity=0, count=0):
    """Return a dict of statistical properties (metadata) for a database column (model field)

    Strings are UTF-8 encoded (UTF-16 or invalid UTF-8 characters are ignored)
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
        try:
            field_properties['num_distinct'] = queryset.values(field.name).distinct().count()
            field_properties['num_null'] = queryset.filter(**{'%s__isnull' % field.name: True}).count()
            field_properties['fraction_distinct'] = float(field_properties['num_distinct']) / (count or 1)
        except DatabaseError as e:
            if verbosity:
                print_exc()
                print "DatabaseError: Skipped count of values in field named '%s' (%s) because of %s." % (field.name, repr(field.db_column), e)
            connection.close()
        try:
            if field_properties['num_distinct'] > 1 and (0 < field_properties['fraction_distinct'] < 0.999):
                # this will not work until pyodbc is updated
                # May be related to django-pyodbc incompatability with django 1.6
                # FIXME: use the working query for values.distinct.count and sort that dict and then query the top 10 of those individually
                field_properties['most_frequent'] = [(v, c) for (v,c) in 
                                                     queryset.distinct().values(field.name).annotate(field_value_count=models.Count(field.name))
                                                     .extra(order_by=['-field_value_count']).values_list(field.name, 'field_value_count')
                                                     [:min(field_properties['num_distinct'], 10)]
                                                    ]
        except (StandardError, FieldError, DatabaseError) as e:
            if verbosity:
                print "Warning: Failed to calculate the Top-10 histogram for field named '%s' (%s) because of %s." % (field.name, repr(field.db_column), e)
            if verbosity > 2:
                print_exc()

    field_properties['max'] = None
    field_properties['min'] = None
    # check field_properties['num_null'] for all Null first?
    if count and typ and typ not in types_not_aggregatable:
        connection.close()
        try:
            field_properties['max'] = clean_utf8(queryset.aggregate(max_value=models.Max(field.name))['max_value'])
            field_properties['min'] = clean_utf8(queryset.aggregate(min_value=models.Min(field.name))['min_value'])
        except ValueError as e:
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


def index_with_dupes(values_list, unique_together=2, model_number_i=0, serial_number_i=1, verbosity=1):
    '''Create dict from values_list with first N values as a compound key.

    Default N (number of columns assumbed to be "unique_together") is 2.
    >>> index_with_dupes([(1,2,3), (5,6,7), (5,6,8), (2,1,3)]) == ({(1, 2): (1, 2, 3), (2, 1): (2, 1, 3), (5, 6): (5, 6, 7)}, {(5, 6): [(5, 6, 7), (5, 6, 8)]})
    True
    '''
    try:
        N = values_list.count()
    except:
        N = len(values_list)
    if verbosity:
        print 'Indexing %d values_lists in a queryset or a sequence of Django model instances (database table rows).' % N
    index, dupes = {}, {}
    pbar = None
    if verbosity and N > min(1000000, max(0, 100000**(1./verbosity))):
        widgets = ['%d rows: ' % N, Percentage(), ' ', RotatingMarker(), ' ', Bar(),' ', ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=len(values_list)).start()
    rownum = 0
    for row in values_list:
        normalized_key = [str(row[model_number_i]).strip(), str(row[serial_number_i]).strip()]
        normalized_key += [i for i in range(unique_together) if i not in (serial_number_i, model_number_i)]
        normalized_key = tuple(normalized_key)
        if normalized_key in index:
            # need to add the first nondupe before we add the dupes to the list
            if normalized_key not in dupes:
                dupes[normalized_key] = [index[normalized_key]]
            dupes[normalized_key] = dupes[normalized_key] + [row]
            if verbosity > 2:
                print 'Duplicate model-serial number found. Here are all the rows that match this key:'
                print dupes[normalized_key]
        else:
            index[normalized_key] = row 
        if pbar:
            pbar.update(rownum)
        rownum += 1
    if pbar:
        pbar.finish()
    if verbosity:
        print 'Found %d duplicate model-serial pairs in the %d records or %g%%' % (len(dupes), len(index), len(dupes)*100./(len(index) or 1.))
    return index, dupes


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


def make_serializable(data, mutable=True):
    r"""Make sure the data structure is json serializable (json.dumps-able), all they way down to scalars in nested structures.

    If mutable=False then return tuples for all iterables, except basestrings (strs),
        so that they can be used as keys in a Mapping (dict).

    >>> from collections import OrderedDict
    >>> from decimal import Decimal
    >>> data = {'x': Decimal('01.234567891113151719'), 'X': [{('y', 'z'): {'q': 'A\xFFB'}}, 'ender'] }
    >>> make_serializable(OrderedDict(data)) == {'X': [{('y', 'z'): {'q': 'A\xc3\xbfB'}}, 'ender'], 'x': 1.2345678911131517}
    True
    """
    #print 'serializabling: ' + repr(data)
    # print 'type: ' + repr(type(data))
    if isinstance(data, basestring):
        return clean_utf8(data)
    if isinstance(data, (datetime.datetime, datetime.date, datetime.time)):
        return str(data)
    #print 'nonstring type: ' + repr(type(data))
    if isinstance(data, Mapping):
        mapping = tuple((make_serializable(k, mutable=False), make_serializable(v, mutable=mutable)) for (k, v) in data.iteritems())
        # print 'mapping tuple = %s' % repr(mapping)
        #print 'keys list = %s' % repr([make_serializable(k, mutable=False) for k in data])
        # this mutability business is probably unneccessary because the keys of the mapping will already be immutable... at least until python 3 MutableMappings
        if mutable:
            return dict(mapping)
        return mapping
    if hasattr(data, '__iter__'):
        if mutable:
            #print list(make_serializable(v, mutable=mutable) for v in data)
            return list(make_serializable(v, mutable=mutable) for v in data)
        else:
            #print tuple(make_serializable(v, mutable=mutable) for v in data)
            return tuple(make_serializable(v, mutable=mutable) for v in data)
    if isinstance(data, (float, Decimal)):
        return float(data)
    try:
        return int(data)
    except:
        try:
            return float(data)
        except:
            try:
                # try to parse a date or datetime string
                return parser.parse(str(data))
            except:
                return str(try_convert(data))


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


def clean_utf8(byte_string, carefully=False):
    r"""Delete any invalid symbols in a UTF-8 encoded string

    Returns the cleaned string.
    
    >>> clean_utf8('`A\xff\xffBC\x7fD\tE\r\nF~G`')
    '`A\xc3\xbf\xc3\xbfBC\x7fD\tE\r\nF~G`'
    >>> clean_utf8('`A\xff\xffBC\x7fD\tE\r\nF~G`', carefully=True)
    '`ABC\x7fD\tE\r\nF~G`'
    """
    #print 'cleaning: ' + repr(byte_string)
    if not isinstance(byte_string, basestring):
        return byte_string
    if carefully:
        while True:
            try:
                byte_string.decode('utf8')
                # json.dumps(byte_string)
                break
            except UnicodeDecodeError as e:
                    m = re.match(r".*can't[ ]decode[ ]byte[ ]0x[0-9a-fA-F]{2}[ ]in[ ]position[ ](\d+)[ :.].*", str(e))
                    if m and m.group(1):
                        i = int(m.group(1))
                        byte_string = byte_string[:i] + byte_string[i+1:]
                    else:
                        raise e
        return byte_string
    else:
        # print 'not carefully'
        diagnosis = chardet.detect(byte_string)
        # print diagnosis
        if diagnosis['confidence'] > 0.5:
            try:
                #print diagnosis
                #print 'detected and cleaned: ' + repr(byte_string.decode(diagnosis['encoding']).encode('utf8'))
                return str(byte_string.decode(diagnosis['encoding']).encode('utf8'))
            except:
                pass
        try:
            # Japanese corporations often use 'SQL_Latin1_General_CP1_CI_AS', a case-insensitive mix of CP-1252 and UTF-8
            try:
                # print 'CP1252'
                #print byte_string.decode('CP-1252')
                return str(byte_string.decode('CP-1252').encode('utf8'))
            # MS SQL Server default encoding
            except:
                return str(byte_string.decode('iso-8859-1').encode('utf8'))
        except:
            pass
        try:
            #print 'utf-16'
            return str(byte_string.decode('utf16').encode('utf8'))
        except:
            pass
    #print 'failed to clean: ' + repr(byte_string)
    return str(byte_string)


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
    r"""Based on https://github.com/jfalkner/Efficient-Django-QuerySet-Use

    >>> from pug.miner.models import Database
    >>> qt = QueryTimer()
    >>> print 'If this fails, you may need to `manage.py syncdb`: %r' % list(Database.objects.values()[:1])  # doctest: +ELLIPSIS
    If this fails, you may need to `manage.py syncdb`:...
    >>> qt.stop()  # doctest: +ELLIPSIS
    QueryTimer(time=0.0..., num_queries=...)
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


# TODO: make this a django filter query of a database rather than a generator
def count_unique(table, field=-1):
    """Use the Django ORM or collections.Counter to count unique values of a field in a table

    `table` is one of:
    1. An iterable of Django model instances for a database table (e.g. a Django queryset)
    2. An iterable of dicts or lists with elements accessed by row[field] where field can be an integer or string
    3. An iterable of objects or namedtuples with elements accessed by `row.field`

    `field` can be any immutable object (the key or index in a row of the table that access the value to be counted)
    """
    from collections import Counter

    # try/except only happens once, and fastest route (straight to db) tried first
    try:
        ans = {}
        for row in table.distinct().values(field).annotate(field_value_count=models.Count(field)):
            ans[row[field]] = row['field_value_count']
        return ans
    except:
        try:
            return Counter(row[field] for row in table)
        except:
            try:
                return Counter(row.get(field, None) for row in table)
            except:
                try:
                    return Counter(row.getattr(field, None) for row in table)
                except:
                    pass