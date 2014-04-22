
import datetime
from collections import OrderedDict, Mapping
import re
from types import ModuleType
import sqlparse
import os
import csv
import json
from traceback import print_exc

from progressbar import ProgressBar, Percentage, RotatingMarker, Bar, ETA
from fuzzywuzzy import process as fuzzy
import numpy as np
import logging
logger = logging.getLogger('bigdata.info')


DEFAULT_DB = 'default'
DEFAULT_APP = None  # models.get_apps()[-1]
DEFAULT_MODEL = None  # DEFAULT_MODEL.get_models()[0]
from django.core.exceptions import ImproperlyConfigured
models, connection, settings = None, None, None
try:
    from django.db import models
    from django.db import connection
    from django.conf import settings  # there is only one function that requires settings, all other functions should be moved to nlp.db module?
except ImproperlyConfigured:
    import traceback
    print traceback.format_exc()
    print 'WARNING: The module named %r from file %r' % (__name__, __file__)
    print '         can only be used within a Django project!'
    print '         Though the module was imported, some of its functions may raise exceptions.'


import util  # import transposed_lists #, sod_transposed, dos_from_table
from .words import synonyms
from .util import listify
from .db import sort_prefix, consolidated_counts, sorted_dict_of_lists, lagged_seq, NULL_VALUES, NAN_VALUES, BLANK_VALUES
from pug.nlp.db import clean_utf8

#from pug.nlp.util import make_int, dos_from_table  #, sod_transposed
#from pug.db.explore import count_unique, make_serializable
#from pug.nlp import util
#from pug.nlp import djdb


class QueryTimer(object):
    """Based on https://github.com/jfalkner/Efficient-Django-QuerySet-Use

    >>> from miner.models import TestModel
    >>> qt = QueryTimer()
    >>> cm_list = list(TestModel.objects.values()[0:10])
    >>> qt.stop()  # doctest: +ELLIPSIS
    QueryTimer(time=0.0..., num_queries=1)
    """

    def __init__(self, time=None, num_queries=None, sql=''):
        self.time, self.num_queries = time, num_queries
        self.start_time, self.start_queries = None, None
        self.sql = sql
        self.start()

    def start(self):
        self.queries = []
        self.start_time = datetime.datetime.now()
        self.start_queries = len(connection.queries)

    def stop(self):
        self.time = (datetime.datetime.now() - self.start_time).total_seconds()
        self.queries = connection.queries[self.start_queries:]
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


def normalize_values_queryset(values_queryset, model=None, app=None):
    model = model or values_queryset.model
    app = app or DEFAULT_APP
    new_list = []
    for record in values_queryset:
        new_record = {}
        for k, v in record.iteritems():
            field_name = find_field(k, model=model, app=app)
            field_class = model._meta.get_field(field_name)
            # if isinstance(field_class, (models.fields.DateTimeField, models.fields.DateField)):
            #     new_record[field_name] = unix_timestamp(v)
            # try:
            if isinstance(field_class, (models.fields.CharField, models.fields.TextField))  or isinstance(v, basestring):
                if v is None:
                    v = ''
                else:
                    v = unicode(v).strip()
            if isinstance(field_class, models.fields.CharField):
                if len(v) > getattr(field_class, 'max_length', 0):
                    print k, v, len(v), '>', field_class.max_length
                    print 'string = %s' % repr(v)
                    # truncate strings that are too long for the database field
                    v = v[:getattr(field_class, 'max_length', 0)]
            new_record[field_name] = v
            # except:
            #     pass
            if (v is None or new_record[field_name] is None) and not getattr(field_class, 'null'):
                new_record[field_name] = ''
        print new_record
        new_list += [new_record]
    return new_list


# TODO: use both get and set to avoid errors when different values chosen
# TODO: modularize in separate function that finds CHOICES appropriate to a value key
def normalize_choices(db_values, field_name, app=DEFAULT_APP, model_name='', human_readable=True, none_value='Null', blank_value='Unknown', missing_value='Unknown DB Code'):
    if app and isinstance(app, basestring):
        app = get_app(app)
    if not db_values:
        return
    try:
        db_values = dict(db_values)
    except:
        raise NotImplemented("This function can only handle objects that can be converted to a dict, not lists or querysets returned by django `.values().aggregate()`.")

    if not field_name in db_values:
        return db_values
    if human_readable:
        for i, db_value in enumerate(db_values[field_name]):
            if db_value in (None, 'None') or app in (None, 'None'):
                db_values[field_name][i] = none_value
                continue
            if isinstance(db_value, basestring):
                normalized_code = str(db_value).strip().upper()
            # the app is actually the models.py module, NOT the app_name package
            # so don't look in app.models, you'll only find django.db.models there (app_name.models.models)
            choices = getattr(app, 'CHOICES_%s' % field_name.upper(), [])
            normalized_name = None
            if choices:
                normalized_name = str(choices.get(normalized_code, missing_value)).strip()
            elif normalized_code:
                normalized_name = 'DB Code: "%s"' % normalized_code
            db_values[field_name][i] = normalized_name or blank_value
    else:
        raise NotImplemented("This function can only convert database choices to human-readable strings.")
    return db_values


def get_app(app=None, verbosity=0):
    """Uses django.db.models.get_app and fuzzywuzzy to get the models module for a django app

    Retrieve an app module from an app name string, even if mispelled (uses fuzzywuzzy to find the best match)
    To get a list of all the apps use `get_app(None)` or `get_app([]) or get_app(())`
    To get a single random app use `get_app('')`

    >>> get_app('call').__class__.__name__ == 'module'
    True
    >>> get_app('model').__name__ == 'miner.models'
    True
    >>> isinstance(get_app('whatever'), ModuleType)
    True
    >>> isinstance(get_app(''), ModuleType)
    True
    isinstance(get_app(), ModuleType)
    False
    isinstance(get_app(), list)
    True
    """
    # print 'get_app(', app
    if not app:
        # for an empty list, tuple or None, just get all apps
        if isinstance(app, (type(None), list, tuple)):
            return [app_class.__package__ for app_class in models.get_apps() if app_class and app_class.__package__]
        # for a blank string, get the default app(s)
        else:
            if get_app.default:
                return get_app(get_app.default)
            else:
                return models.get_apps()[-1]
    if isinstance(app, basestring) and app.strip().endswith('.models'):
        return get_app(app[:-len('.models')])
    if isinstance(app, ModuleType):
        return app
    # print 'type(' + repr(app) + ') = ' + repr(type(app))
    try:
        if verbosity > 1:
            print 'Attempting django.models.get_app(%r)' % app
        return models.get_app(app)
    except:
        print_exc()
        if not app:
            if verbosity:
                print 'WARNING: app = %r, so returning None!' % app
            return None
    if verbosity > 2:
        print 'Trying a fuzzy match on app = %r' % app
    app_names = [app_class.__package__ for app_class in models.get_apps() if app_class and app_class.__package__]
    fuzzy_app_name = fuzzy.extractOne(str(app), app_names)[0]
    if verbosity:
        print 'WARNING: Best fuzzy match for app name %r is %s' % (app, fuzzy_app_name)
    return get_app(fuzzy_app_name)
get_app.default = DEFAULT_APP


def get_model(model=DEFAULT_MODEL, app=DEFAULT_APP):
    """
    >>> from django.db import connection
    >>> connection.close() 
    >>> get_model('WikiI').__name__.startswith('WikiItem')
    True
    >>> connection.close() 
    >>> isinstance(get_model('master'), models.base.ModelBase)
    True
    >>> connection.close() 
    >>> get_model(get_model('CaseMaster', DEFAULT_APP)).objects.count() >= 0
    True
    """
    # print 'get_model' + repr(model) + ' app ' + repr(app)
    if isinstance(model, models.base.ModelBase):
        return model
    app = get_app(app)
    try:
        model_object = models.get_model(app, model)
        if model_object:
            return model_object
    except:
        pass
    app = get_app(app)
    if not app:
        return None
    model_names = [mc.__name__ for mc in models.get_models(app)]
    if app and model and model_names:
        return models.get_model(app.__package__.split('.')[-1], fuzzy.extractOne(str(model), model_names)[0])


def get_db_alias(app=DEFAULT_APP):
    if app:
        if isinstance(app, basestring) and str(app).strip():
            if settings and str(app).strip() in settings.DATABASES:
                return str(app).strip()
            else:
                return None
        app = get_app(app)
    try:
        return get_db_alias(app.__package__)  # app.__name__.split('.')[0]
    except:
        return DEFAULT_DB


def field_cov(fields, models, apps):
    columns = util.get_columns(fields, models, apps)
    columns = util.make_real(columns)
    return np.cov(columns)


def queryset_from_title_prefix(title_prefix=None, model=DEFAULT_MODEL, app=DEFAULT_APP):
    filter_dict = {}
    if isinstance(title_prefix, basestring):
        if title_prefix.lower().endswith('quantity'):
            filter_dict = {'title__startswith': title_prefix[:-5].rstrip('_')}
            model = 'WikiItem'
        else:
            model = model or DEFAULT_MODEL
    
    return queryset_from_filter_dict(filter_dict, model, app)


def queryset_from_filter_dict(filter_dict=None, model=None, app=None):
    """TODO: add fuzzy app, model and field (filter key) matching"""
    model = model or DEFAULT_MODEL
    app = app or DEFAULT_APP
    model = get_model(model, app)
    
    if filter_dict:
        return model.objects.filter(**filter_dict)
    return model.objects


def querysets_from_title_prefix(title_prefix=None, model=DEFAULT_MODEL, app=DEFAULT_APP):
    """Return a list of Querysets from a list of model numbers"""

    if title_prefix is None:
        title_prefix = [None]

    filter_dicts = []
    model_list = []
    if isinstance(title_prefix, basestring):
        title_prefix = title_prefix.split(',')
    elif not isinstance(title_prefix, dict):
        title_prefix = title_prefix
    if isinstance(title_prefix, (list, tuple)):
        for i, title_prefix in enumerate(title_prefix):
            if isinstance(title_prefix, basestring):
                if title_prefix.lower().endswith('sales'):
                    title_prefix = title_prefix[:-5].strip('_')
                    title_prefix += [title_prefix]
                    model_list += ['WikiItem']
                else:
                    model_list += [DEFAULT_MODEL]
            filter_dicts += [{'model__startswith': title_prefix}]
    elif isinstance(title_prefix, dict):
        filter_dicts = [title_prefix]
    elif isinstance(title_prefix, (list, tuple)):
        filter_dicts = listify(title_prefix)
    
    model = get_model(model, app)

    querysets = []
    for filter_dict, model in zip(filter_dicts, model_list):
        filter_dict = filter_dict or {}
        querysets += [model.objects.filter(**filter_dict)]


def data_into_model(table, model, fields=('referrer', 'country', 'read_faq', 'pages_viewed', 'service'), app=DEFAULT_APP):
    model = get_model(model)

    if not fields:
        fields = table[0]
        del(table[0])
        #fields = (field for field in model._meta.get_all_field_names())
    
    for row in table:
        kwargs = {}
        for i, field in enumerate(fields):
            kwargs[field] = row[i]
        model.objects.get_or_create(**kwargs)


def values(fields=None, filter_dict=None, model=DEFAULT_MODEL, app=DEFAULT_APP, transpose=False):
    if filter_dict and not fields:
        fields = [field.split('_')[0] for field in filter_dict] 
    qs = queryset_from_filter_dict(filter_dict, model, app)
    qs = qs.objects.values(*listify(fields))
    qs = [[rec[k] for k in rec] for rec in qs]
    if transpose:
        return util.transposed_lists(qs)
    return qs


def format_fields(x, y, filter_dict={'model__startswith': 'LC60'}, model=DEFAULT_MODEL, app=DEFAULT_APP, count_x=None, count_y=None, order_by=None, limit=1000, aggregate=None, sum_x=None, sum_y=None):
    model = get_model(model, app)
    
    if order_by in ('x', 'y', '+x', '+y', '-x', '-y', x, y, '+' + x, '+' + y, '-' + x, '-' + y):
        order_by += '_value'

    if isinstance(x, basestring):
        count_x = bool(count_x) or x.endswith('__count')
        count_y = bool(count_y)or y.endswith('__count')
        objects = model.objects.filter(**filter_dict)
        if aggregate:
            objects = objects.extra({'x_value': aggregate})
            objects = objects.values('x_value')
            x = 'x_value'
            objects = objects.annotate(y_value=models.Count('pk'))
            y = 'y_value'
        else:
            if count_x:
                objects = objects.annotate(x_value=models.Count(x))
                x = 'x_value'
            if count_y:
                objects = objects.annotate(y_value=models.Count(y))
                y = 'y_value'
            if sum_x:
                objects = objects.annotate(x_value=models.Sum(x))
                x = 'x_value'
            if sum_y:
                objects = objects.annotate(y_value=models.Sum(y))
                y = 'y_value'
        objects = objects.values(x, y)
        if order_by:
            objects = objects.order_by(order_by)
        objects = objects.all()
        if limit:
            objects = objects[:limit]
    return util.sod_transposed(objects)



def count_in_category(x='call_type', filter_dict=None, model=DEFAULT_MODEL, app=DEFAULT_APP, sort=True, limit=1000):
    """
    Count the number of records for each discrete (categorical) value of a field and return a dict of two lists, the field values and the counts.

    >>> x, y = count_in_category(x='call_type', filter_dict={'model__startswith': 'LC60'}, limit=5, sort=1)
    >>> len(x) == len(y) == 5
    True
    >>> y[1] >= y[0]
    True
    """
    sort = sort_prefix(sort)
    model = get_model(model, app)
    filter_dict = filter_dict or {}

    x = fuzzy.extractOne(str(x), model._meta.get_all_field_names())[0]    

    objects = model.objects.filter(**filter_dict)
    objects = objects.values(x)
    objects = objects.annotate(y=models.Count(x))
    if sort is not None:
        objects = objects.order_by(sort + 'y')
    objects = objects.all()
    if limit:
        objects = objects[:int(limit)]
    objects = normalize_choices(util.sod_transposed(objects), field_name=x, app=app, human_readable=True)
    if not objects:
        return None
    objects = consolidated_counts(objects, field_name=x, count_name='y')
    if sort is not None:
        objects = sorted_dict_of_lists(objects, field_names=['y', x], reverse=bool(sort))
    return objects[x], objects['y']


def count_in_date(x='date_time', filter_dict=None, model=DEFAULT_MODEL, app=DEFAULT_APP, sort=True, limit=100000):
    """
    Count the number of records for each discrete (categorical) value of a field and return a dict of two lists, the field values and the counts.

    >>> from django.db import connection
    >>> connection.close()
    >>> x, y = count_in_date(x='date', filter_dict={'model__icontains': 'LC5'}, limit=5, sort=1)
    >>> len(x) == len(y) == 5
    True
    >>> y[1] >= y[0]
    True
    """
    sort = sort_prefix(sort)
    model = get_model(model, app)
    filter_dict = filter_dict or {}

    x = fuzzy.extractOne(str(x), model._meta.get_all_field_names())[0]    

    objects = model.objects.filter(**filter_dict)
    objects = objects.extra({'date_bin_for_counting': 'date(%s)' % x})
    objects = objects.values('date_bin_for_counting')
    objects = objects.annotate(count_of_records_per_date_bin=models.Count('pk'))
    
    # FIXME: this duplicates the dict of lists sort below
    if sort is not None:
        objects = objects.order_by(sort + 'date_bin_for_counting')
    objects = objects.all()
    if limit:
        objects = objects[:int(limit)]
    objects = util.sod_transposed(objects)
    if sort is not None:
        objects = sorted_dict_of_lists(objects, field_names=['count_of_records_per_date_bin', 'date_bin_for_counting'], reverse=bool(sort))
    #logger.info(x)
    return objects['date_bin_for_counting'], objects['count_of_records_per_date_bin']


def sum_in_date(x='date', y='net_sales', filter_dict=None, model='WikiItem', app=DEFAULT_APP, sort=True, limit=100000):
    """
    Count the number of records for each discrete (categorical) value of a field and return a dict of two lists, the field values and the counts.

    >>> from django.db import connection
    >>> connection.close()
    >>> x, y = sum_in_date(y='net_sales', filter_dict={'model__startswith': 'LC60'}, model='WikiItem', limit=5, sort=1)
    >>> len(x) == len(y) == 5
    True
    >>> y[1] >= y[0]
    True
    """
    sort = sort_prefix(sort)
    model = get_model(model, app)
    filter_dict = filter_dict or {}
    objects = model.objects.filter(**filter_dict)
    # only the x values are now in the queryset (datetime information)
    objects = objects.values(x)
    objects = objects.annotate(y=models.Sum(y))

    if sort is not None:
        # FIXME: this duplicates the dict of lists sort below
        objects = objects.order_by(sort + 'y')
    objects = objects.all()
    if limit:
        objects = objects[:int(limit)]
    objects = util.sod_transposed(objects)
    if sort is not None:
        objects = sorted_dict_of_lists(objects, field_names=['y', x], reverse=bool(sort=='-'))
    if not x in objects or not 'y' in objects:
        return [], []
    else:
        return objects[x], objects['y']

def sequence_from_filter_spec(field_names, filter_dict=None, model=DEFAULT_MODEL, app=DEFAULT_APP, sort=None, limit=5000):
    field_names = listify(field_names)
    # TODO: enable +1 to mean increasing order on 1st column
    sort_char = sort_prefix(sort)
    model = get_model(model, app)
    filter_dict = filter_dict or {}
    objects = model.objects.filter(**filter_dict)
    # only the x values are now in the queryset (datetime information)
    objects = objects.values(*field_names)
    if sort is not None:
        # FIXME: this duplicates the dict of lists sort below
        objects = objects.order_by(sort_char + field_names[-1])
    objects = objects.all()
    if limit:
        objects = objects[:int(limit)]
    objects = util.sod_transposed(objects)
    if sort is not None:
        if len(field_names) > 1:
            objects = sorted_dict_of_lists(objects, field_names=[field_names[-1]] + field_names[:-1], reverse=bool(sort_prefix))
        else:
            objects = sorted_dict_of_lists(objects, field_names=field_names, reverse=bool(sort))
    return tuple(objects[fn] for fn in field_names)


def find_fields(fields, model=DEFAULT_MODEL, app=DEFAULT_APP, score_cutoff=50, pad_with_none=False):
    """
    >>> find_fields(['date_time', 'title_prefix', 'sales'], model='WikiItem')
    ['date', 'model', 'net_sales']
    """
    fields = listify(fields)
    model = get_model(model, app)
    available_field_names = model._meta.get_all_field_names()
    matched_fields = []
    for field_name in fields:
        match = fuzzy.extractOne(str(field_name), available_field_names)
        if match and match[1] is not None and match[1] >= score_cutoff:
            matched_fields += [match[0]]
        elif pad_with_none:
            matched_fields += [None]
    return matched_fields


def find_synonymous_field(field, model=DEFAULT_MODEL, app=DEFAULT_APP, score_cutoff=50, root_preference=1.02):
    """
    >>> find_synonymous_field('date', model='WikiItem')
    'end_date_time'
    >>> find_synonymous_field('date', model='WikiItem')
    'date_time'
    >>> find_synonymous_field('time', model='WikiItem')
    'date_time'
    """
    fields = listify(field) + list(synonyms(field))
    model = get_model(model, app)
    available_field_names = model._meta.get_all_field_names()
    best_match, best_ratio = None, None
    for i, field_name in enumerate(fields):
        match = fuzzy.extractOne(str(field_name), available_field_names)
        # print match
        if match and match[1] >= score_cutoff:
            if not best_match or match[1] > (root_preference * best_ratio):
                best_match, best_ratio = match
    return best_match


def find_field(field, model=DEFAULT_MODEL, app=DEFAULT_APP, score_cutoff=50):
    """
    >>> find_field('date_time', model='WikiItem')
    'date'
    >>> find_field('$#!@', model='WikiItem')
    >>> find_field('date', model='WikiItem')
    'end_date_time'
    >>> find_field('date', model='WikiItem')
    'date_in_svc'
    >>> find_synonymous_field('date', model='WikiItem')
    'date_time'
    """
    return find_fields(field, model, app, score_cutoff, pad_with_none=True)[0]


def lagged_in_date(x=None, y=None, filter_dict=None, model='WikiItem', app=DEFAULT_APP, sort=True, limit=5000, lag=1, pad=0, truncate=True):
    """
    Lag the y values by the specified number of samples.

    FIXME: sort has no effect when sequences provided in x, y instead of field names

    >>> lagged_in_date(x=[.1,.2,.3,.4], y=[1,2,3,4], limit=4, lag=1)
    ([0.1, 0.2, 0.3, 0.4], [0, 1, 2, 3])
    >>> lagged_in_date(x=[.1,.2,.3,.4], y=[1,2,3,4], lag=1, truncate=True)
    ([0.1, 0.2, 0.3, 0.4], [0, 1, 2, 3])
    """
    lag = int(lag or 0)
    #print 'X, Y:', x, y
    if isinstance(x, basestring) and isinstance(y, basestring):
        x, y = sequence_from_filter_spec([find_synonymous_field(x), find_synonymous_field(y)], filter_dict, model=model, app=app, sort=sort, limit=limit)
    if y and len(y) == len(x):
        if sort:
            xy = sorted(zip(x,y), reverse=bool(int(sort) < 0))
            x, y = [col1 for col1, col2 in xy], [col2 for col1, col2 in xy]
        return x, lagged_seq(y, lag=lag, pad=pad, truncate=truncate)
    if x and len(x) and 2 == len(x) <= len(x[0]):
        #print 'X:', x
        x, y = x[0], lagged_seq(x[1], lag=lag, pad=pad, truncate=truncate)
        if truncate:
            print truncate, lag
            if lag >= 0:
                x = x[lag:]
            else:
                x = x[:lag]
        #print x, y
    return x, y

def get_column(field, model, filter_dict, app):
    qs = queryset_from_filter_dict(filter_dict, model, app)
    #if field in qs._meta.fields
    return [obj[field] for obj in qs.values(field)]


def get_columns(fields, models, filter_dicts, apps):
    fields = listify(fields)
    N = len(fields)
    models = listify(models, N) or [None] * N
    filter_dicts= listify(filter_dicts, N) or [{}] * N
    apps = listify(apps, N) or [None] * N
    columns = []
    for field, model, app, filter_dict in zip(fields, models, filter_dicts, apps):
        columns += [get_column(field, model, filter_dict, app)]


class Columns(OrderedDict):
    """An OrderedDict of named columns of data
         `OrderedDict([('name1', [x11, x21, ..., xM1]), ... ('nameM', [x1, ... objNM])]`
          similar to a Pandas `DataFrame`, but with the added convenience functions for DB I/O
          and numpy data processing

    keys of OrderedDict are the column (db field) names
        prefixed with the app and and table name if ambiguous
    The attribute `Columns.db_fields` is an OrderedDict which stores a list of tuples 
        `(app_name, table_name, column_name, db_filter_dict)` 
        using the same keys as the Columns OrderedDict data container

    values of the OrderedDict
    """
    default_app = DEFAULT_APP
    default_table = DEFAULT_MODEL
    # FIXME: default args need to be replaced by None and this value substituted, if necessary
    default_ddof = 0
    default_tall = True
    db_fields = None
    len_column = None

    def __init__(self, *args, **kwargs):
        fields = listify(kwargs.get('fields', None), N=self.len_column)
        filters = listify(kwargs.get('filters', None), N=self.len_column)
        tables = listify(kwargs.get('tables', None), N=self.len_column)
        apps = listify(kwargs.get('apps', None), N=self.len_column)

        super(Columns, self).__init__()
        # TODO: DRY up the redundancy
        for arg_name in ('fields', 'filters', 'tables', 'apps'):
            locals()[arg_name] = listify(locals()[arg_name], N=self.len_column)
            self.len_column = max(self.len_column, len(locals()[arg_name]))

        kwargs = self.process_kwargs(kwargs, prefix='default_', delete=True)

        split_fields = [re.split(r'\W|__', field, maxsplit=3) for field in fields]
        if filters and not fields:
            split_fields = [re.split(r'\W|__', iter(d).next(), maxsplit=3) for d in filters]

        for i, arg_name in enumerate(('apps', 'tables', 'fields')):
            if not locals()[arg_name]:
                locals()[arg_name] = listify((sf[min(i, len(sf) - 1)] for sf in split_fields), N=self.len_column)
        
        if not apps or not apps[0] or apps[0].strip() == '.':
            apps = listify(self.default_app, self.len_column)
        self.default_app = apps[0]

        self.db_fields = OrderedDict((fields[i], (apps[i], tables[i], fields[i], filters[i])) for i in range(self.len_column))

        if len(args) == 1:
            if isinstance(args[0], basestring):
                self.from_string(args[0])
            elif isinstance(args[0], models.query.ValuesQuerySet) or hasattr(args[0], '__iter__'):
                if isinstance(iter(args[0]).next(), Mapping):
                    self.from_valuesqueryset(args[0])
                else:
                    self.from_row_wise_lists(args[0], **kwargs)
            elif isinstance(args[0], models.query.QuerySet):
                self.from_queryset(args[0])
        if self and len(self) and self.default_tall:
            self.make_tall()

    def process_kwargs(self, kwargs, prefix='default_', delete=True):
        """
        set self attributes based on kwargs, optionally deleting kwargs that are processed
        """
        processed = []
        for k in kwargs:
            if hasattr(self, prefix + k):
                processed += [k]
                setattr(self, prefix + k, kwargs[k])
        for k in processed:
            del(kwargs[k])
        return kwargs

    def from_filter(self, f):
        self.from_queryset(queryset_from_filter_dict(f), self.default_table, self.default_app)
        return self

    def from_fields(self, fields, filter_dict):
        pass

    def from_string(self, s):
        pass

    def from_file(self, f):
        pass

    def from_queryset(self, qs, ignore_fields=('_state',)):
        #super(Columns, self).__init__()
        self.clear()
        for i, rec in enumerate(qs):
            d = rec.__dict__
            for name, value in d.iteritems():
                if name in ignore_fields:
                    continue
                self[name] = self.get(name, []) + [value]
        self.len_column = min(len(self[i]) for i in self)
        return self

    def from_dict_list(self, dl):
        #super(Columns, self).__init__()
        self.clear()
        for i, d in enumerate(dl):
            if not i:
                for name in d:
                    self[name] = []
            for field, value in d.iteritems():
                self[field] += [value]
        self.len_column = min(len(self[i]) for i in self)
        return self

    def from_valuesqueryset(self, vqs, header_rows=1):
        names = list(range(100))
        for i, d in enumerate(vqs):
            if not i:
                self.clear()
                for name in d:
                    self[name] = []
                if not isinstance(d, Mapping):
                    if not all(isinstance(name, basestring) for name in self):
                        for name in self:
                            del(self[name])
                        for j, val in enumerate(d):
                            self[j] = val
                    names = list(self)
                    # the first row has already been processed (as either column names or column values), so move right along
                    continue
            if not isinstance(d, Mapping):
                for j, value in enumerate(d):
                    try:
                        self[names[j]] += [value]
                    except:
                        # FIXME: this will fail on a list of lists of floats
                        self[j] += [value]
            # TODO: use `iter(vqs)` and .next() to read the first row separtely and branch for the type of d outside of the loop
            else:
                for field in d:
                    self[field] += [d[field]]
        self.len_column = min(len(self[i]) for i in self)
        return self

    def from_row_wise_lists(self, lol, header_rows=0, transpose=False, names=None):
        """Create column-wise Columns object from a row-wise table (list of lists).

        Useful for reading a CSV file."""
        #print '-'*10
        #super(Columns, self).__init__()
        self.clear()
        #print(list(self))
        self.len_column = None

        if header_rows:
            raise NotImplementedError("I don't know how to handle header rows yet")
            return self

        if not lol or not hasattr(lol, '__iter__') or not iter(lol).next():
            return self.from_row_wise_lists([lol], header_rows, transpose, names)


        # if the input is just a 1-D sequence then load it all into one column or one row
        if not hasattr(iter(lol).next(), '__iter__'):
            return self.from_row_wise_lists(tuple([tuple([row]) for row in lol]), header_rows, transpose, names)
        #print '='*20
        #print list(self)
        for i, d in enumerate(lol):
            #print i
            if not i:
                for j, value in enumerate(d):
                    self[j] = [value]
                    #print '-',j
            else:
                for j, value in enumerate(d):
                    self[j] += [value]
                    #print '-',j
        #print list(self)
        try:
            self.len_column = min(len(self[i]) for i in self)
        except:
            self.len_column = None
        #print self
        return self

    def from_column_wise_lists(self, lol, header_rows=0, transpose=False, names=None):
        """Create column-wise Columns object from a row-wise table (list of lists).
        """
        #super(Columns, self).__init__()
        self.clear()
        self.len_column = None

        if transpose:
            return self.from_row_wise_lists(lol, header_rows, transpose=False, names=None)
        names = names or [j for j, column in enumerate(lol)]
        for i, col in enumerate(lol):
            self[names[i]] = [value for value in col]
        self.len_column = min(len(self[i]) for i in self)
        return self

    def make_real(self, default_value=0., null_value=None, blank_value=0., nan_value=0.):
        for name in self:
            for j, val in enumerate(self[name]):
                if val in NULL_VALUES:
                    self[name][j] = null_value
                elif val in NAN_VALUES:
                    self[name][j] = nan_value
                elif val in BLANK_VALUES:
                    self[name][j] = blank_value
                else:
                    try:
                        self[name][j] = float(util.normalize_scientific_notation(str(val)))
                    except:
                        self[name][j] = default_value
        return self


    def as_column_wise_lists(self, transpose=False):
        """Generator over the columns of lists"""
        # make this a generator of generators?
        if transpose:
            ans = self.from_row_wise_lists(self.as_column_wise_lists(transpose=False))
            return ans
        #print self
        return self.values()

    def as_row_wise_lists(self):
        """Generator over the columns of lists"""
        # make this a generator of generators?
        #print self.as_column_wise_lists
        return util.transposed_lists(self.as_column_wise_lists())

    def as_matrix(self):
        """Alias for .as_column_wise_lists()"""
        return self.as_column_wise_lists()

    def as_matrix_transposed(self):
        return self.as_row_wise_lists()

    def cov(self, ddof=None):
        if ddof is None:
            ddof = self.default_ddof
        else:
            self.default_ddof = ddof
        return np.cov(self.make_tall().make_real().as_column_wise_lists(), ddof=ddof)

    def transposed(self):
        return self.from_row_wise_lists(tuple(self.as_column_wise_lists(transpose=False)))

    def make_tall(self):
        if len(self) and len(self[0]) and len(self) > len(self[0]):
            return self.transposed()
        return self

    def pierson(self, ddof=0):
        """Matrix of pierson linear correlation coefficients (rho values) for each pair of columns

        https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
        >>> Columns([[1, 2, 3], [4, 5, 6]]).pierson()
        [[1.0, 1.0], [1.0, 1.0]]
        >>> Columns([[1, 2, 3], [2.5, 3.5, 4.5]], transpose=True).pierson()
        [[1.0, 1.0], [1.0, 1.0]]
        >>> Columns([[1, 3, 2], [4, 5, 7]], transpose=1).pierson()  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        [[1.0, 0.327326835...], [0.327326835..., 1.0]]
        """
        C = self.cov(ddof=ddof)
        rho = []
        N = len(C)
        for i in range(N):
            rho += [[1.] * N]
        for i in range(N):
            for j in range(i + 1, N):
                rho[i][j] = C[i][j] / (C[i][i] * C[j][j] or 1.) ** 0.5
                rho[j][i] = rho[i][j]
        return rho

    def rho():
        doc = """Matrix of pierson linear correlation coefficients (rho values)."""
        def fget(self):
            return self.pierson(ddof=self.default_ddof)
        # def fset(self, value):
        #    pass
        #def fdel(self):
        #    pass
        return locals()
    rho = property(**rho())

    # def __repr__(self):
    #     return repr(super(Columns, self))

    def best_scale_factor(self, x=0, y=-1, multiple=None):
        if isinstance(x, int) and abs(x) < len(self):
            # this is a dict, not a sequence! so so have to wrap / mod negative indices
            x = self[x % len(self)]
        if isinstance(y, int) and abs(y) < len(self):
            y = self[y % len(self)]
        scale_factor = float(max(abs(min(y)), max(y))) / max(abs(min(x)), max(x))
        if not multiple:
            return scale_factor
        return scale_factor
        # return float(Decimal(int(scale_factor)) / 10).quantize(1, rounding=ROUND_UP) * 10)


def fixture_record_from_row():
    return """{
    "pk": 112799, 
    "model": "crawler.wikiitem", 
    "fields": {
        "count": "{u'child': 1, u'four': 1, u'protest': 1, u'2008-11-11': 1, u'Communist': 1, u'Schuster': 2, u'Foundation': 1, u'calculate': 1, u'LCCN': 1, u'segments': 1, u'Ronald': 2, u'under': 2, u'teaching': 1, u'worth': 1, u'conjecture': 3, u'collaborate': 1, u'Waterloo': 3, u'Henri': 1, u'cashable': 1, u'Famer': 1, u'Memoirs': 1, u'school': 2, u'prize': 3, u'Bacon': 1, u'solution': 1, u'Gy': 1, u'296': 1, u'Paul': 44, u'Babai': 2, u'guidelines': 1, u'approximation': 1, u'elegant': 4, u'likely': 2, u'estimated': 1, u'even': 1, u'nem': 1, u'contributed': 1, u'poison': 1, u'liberated': 1, u'causes': 1, u'increasing': 1, u'whose': 1, u'Items': 1, u'never': 4, u'hundreds': 1, u'active': 2, u'107': 1, u'Engl': 1, u'changed': 1, u'controversy': 1, u'Nathanson': 1, u'Alternative': 1, u'mistake': 2, u'explained': 1, u'Also': 1, u'Book': 9, u'spoke': 1, u'would': 7, u\"world's\": 1, u'music': 1, u'until': 1, u'Biographical': 1, u'V': 2, u'90': 1, u'circumstances': 1, u'1990': 1, u'1993': 2, u'1992': 2, u'1995': 2, u'1994': 1, u'divorced': 1, u'1996': 11, u'1999': 4, u'1998': 3, u'work': 2, u'Steele': 1, u'roof': 1, u'my': 2, u'example': 2, u'Perspectives': 2, u'Gadflies': 1, u'in': 57, u'Ralph': 1, u'Jerry': 5, u'Lip': 1, u'Bruno': 1, u'Frontiers': 2, u'U.S': 3, u'provide': 1, u'Journal': 1, u'copious': 1, u'enp': 1, u'how': 1, u'137643': 1, u'Jack': 1, u'A': 8, u'description': 1, u'after': 4, u'Seife': 1, u'Another': 1, u'enter': 1, u'Ancient': 1, u'Possessions': 1, u'over': 3, u'thesis': 2, u'Robertson': 2, u'before': 4, u'His': 5, u'fit': 1, u'Margulis': 1, u'Birth': 1, u'then': 2, u'zero-dimensional': 1, u'Melvyn': 1, u'they': 2, u'E.F': 1, u'classified': 1, u'l': 4, u'each': 1, u'Agriculture': 1, u'misspellings': 1, u'series': 1, u'Bollobas': 1, u'Springer': 4, u'principled': 1, u\"Oddball's\": 1, u'conjectures': 2, u'Gina': 1, u'rd': 1, u'rf': 1, u'forth': 1, u'disagreements': 1, u'rk': 1, u'turning': 1, u'University': 10, u'little': 2, u'created': 1, u'September': 8, u'National': 1, u'days': 1, u'Human': 1, u'moving': 1, u'Nicolas': 1, u'Combinatorics': 1, u'Please': 1, u'Due': 1, u'Grigory': 1, u'another': 2, u'Ammunition': 1, u'20th-century': 1, u'Academy': 1, u'tov': 1, u'Uncle': 1, u'observations': 1, u'postulate': 1, u'bitter': 1, u'Alexander': 2, u'Search': 1, u'B': 4, u'Genealogy': 2, u'took': 1, u'typographical': 2, u'10.2307': 1, u'amphetamines': 1, u'Encyclop': 1, u\"Erdos's\": 1, u'project': 1, u'matter': 1, u'See': 4, u'050328956': 1, u'Biography': 1, u'seminal': 1, u'Generally': 1, u'pantheon': 1, u'Instead': 1, u'seminar': 1, u'Scholar': 1, u'Then': 2, u'Christian': 1, u'1969': 2, u'1963': 1, u'subjects': 1, u'Available': 1, u'though': 1, u'Vanguard': 1, u'letter': 3, u'grave': 2, u'Jacques': 1, u'doi': 4, u'saying': 2, u'Union': 2, u'solutions': 2, u'Anna': 1, u'just': 2, u'itinerant': 3, u'topological': 1, u'than': 3, u'pursuing': 1, u'announce': 1, u'personality': 1, u'dl': 1, u'Soifer': 2, u'di': 1, u'Nevertheless': 2, u'de': 1, u'stop': 1, u'butulok': 1, u'despite': 2, u'Utcai': 1, u'Soviet': 2, u'Oddball': 1, u'countries': 2, u'fields': 2, u'Washington': 1, u'isreal': 1, u'reference': 1, u'habit': 1, u'Winners': 1, u'9781568584195': 1, u'John': 6, u'best': 3, u'said': 2, u'inappropriate': 1, u'Huberman': 1, u'Aigner': 1, u'09': 1, u'approach': 1, u'C': 2, u'terms': 1, u'dumber': 1, u'topology': 1, u'suggested': 1, u'received': 4, u'country': 1, u'against': 1, u'10.1090': 1, u'17A-6-29': 2, u'10.1098': 1, u'contribution': 1, u'Atiyah': 1, u'epsilons': 1, u'256': 1, u'conference': 1, u'reconsideration': 1, u\"I've\": 1, u'Donat': 1, u'been': 4, u'Early': 2, u'much': 2, u'interest': 1, u'privilege': 1, u'life': 6, u'quantities': 1, u'Poland': 2, u'theorem': 2, u'personally': 1, u'2010-05-29': 3, u'worked': 1, u'pungent': 1, u'say': 1, u'n': 5, u'teachers': 2, u'Zariski': 1, u'buried': 1, u'economics': 1, u'On': 2, u'is': 26, u'it': 6, u'Gazette': 1, u'Heidelberg': 1, u'Retrieved': 11, u'incorrectly': 1, u'several': 4, u'entitled': 1, u'Budapest': 6, u'Residence': 1, u'published': 4, u'practiced': 1, u'DeCastro': 1, u'1979': 1, u'1978': 1, u'1973': 1, u'1971': 1, u'mother': 1, u'Table': 1, u'the': 113, u'Proofs': 2, u'left': 4, u'After': 3, u'proposed': 2, u'unfair': 1, u'Furstenberg': 1, u'assigned': 2, u'Istv': 1, u'Sato': 1, u'Oscar': 1, u'had': 13, u'Hard-to-Win': 1, u'has': 8, u'gave': 1, u'D': 3, u'Britannica': 1, u'birth': 2, u'9780595358403': 1, u'56': 1, u'51': 1, u'50': 1, u'arbitrary': 1, u'Again': 1, u'people': 3, u'born': 2, u'doorstep': 1, u'Life': 1, u'for': 24, u'Simonovits': 1, u'External': 2, u'denied': 1, u'2008-09-01': 1, u'He': 16, u'School': 1, u'who': 9, u\"Bertrand's\": 1, u'Daily': 1, u'Place': 2, u'chapter': 1, u'Gelfand': 1, u'dollars': 1, u'citizens': 1, u'o': 1, u'Ahlfors': 1, u'Still': 1, u'Verlag': 1, u'Feb': 2, u'formerly': 1, u'Scotland': 1, u'intellectual': 1, u'down': 1, u'Aaron': 1, u'donated': 1, u'Hank': 1, u'Extended': 1, u'combinatorics': 3, u'illustrious': 1, u'Approaches': 1, u'Kozma': 1, u'Hans': 1, u'Amer': 1, u'was': 25, u'head': 1, u'offer': 1, u'fascination': 1, u'January': 1, u'Jean': 1, u'true': 1, u'analyst': 1, u'VIAF': 1, u'full': 1, u'different': 1, u'155': 1, u'Variety': 1, u'check': 2, u'Andrey': 1, u'no': 4, u'when': 2, u'Andrew': 1, u'papers': 38, u'Dame': 2, u'E': 1, u'felt': 1, u'Arnold': 2, u'died': 4, u'Estate': 1, u'Charles': 2, u'Keller': 1, u'customary': 1, u'Milner': 1, u'Edited': 1, u'graph': 2, u'father': 2, u'Gap-system.org': 1, u'0': 1, u'finally': 1, u'Burr': 1, u'suffered': 1, u'Secondary': 1, u'Prize': 7, u'Competitions': 1, u'solver': 2, u'did': 4, u'dia': 1, u'McCarthy': 1, u'travels': 1, u'p': 9, u'Kiyoshi': 1, u'Tao': 1, u'George': 5, u'trails': 1, u'Quotable': 1, u'transfinite': 2, u'drinks': 1, u'Bruce': 2, u'Notable': 1, u'Public': 1, u'current': 2, u'525': 1, u'Prizes': 2, u'During': 2, u'filled': 1, u'1913-03-26': 1, u\"s's\": 8, u'Stalin': 1, u'baseball': 1, u'Ltd': 1, u'alone': 1, u'along': 1, u'Times': 2, u'My': 3, u'Dead': 1, u'Ziegler': 1, u'Born': 1, u\"country's\": 1, u'useful': 1, u'When': 1, u'Friedrich': 1, u'anti-Semitism': 1, u'Alberto': 1, u'51768730': 1, u'Hungarian': 9, u'positive': 1, u'give': 3, u'visit': 1, u'Awards': 1, u'https': 1, u'Died': 1, u'October': 1, u'F': 3, u'These': 1, u'Time': 1, u'cases': 1, u'10.1126': 1, u'Lewy': 1, u'lowercase': 1, u'German': 1, u'Anglicization': 1, u'Numbers': 6, u'believed': 1, u'making': 1, u'umlaut': 1, u'Throughout': 1, u'Children': 1, u'stimulating': 1, u'claim': 1, u'Contains': 1, u'Edmund': 1, u'allowed': 1, u'Kruskal': 1, u'Who': 3, u'1': 13, u'nyi': 4, u'147': 1, u'staying': 1, u'fascist': 1, u'eighty': 1, u'Piatetski-Shapiro': 1, u'unclaimed': 1, u'Martin': 1, u'such': 3, u'sz': 1, u'so': 1, u'9780387305264': 1, u'idiosyncratic': 2, u'3-540-22469-6': 1, u'brain': 2, u'episodes': 1, u'Elias': 1, u'argued': 1, u'Hirzebruch': 1, u'still': 1, u'machine': 1, u'Whitney': 1, u'policy': 1, u'main': 1, u'decades': 1, u'into': 3, u'Fej': 3, u'LIBRIS': 1, u'qualified': 1, u'1951': 1, u'1952': 1, u'not': 7, u'nor': 1, u'nos': 1, u'name': 4, u'Pach': 1, u'Transcription': 1, u'year': 1, u'791': 1, u'space': 1, u'Aschbacher': 1, u'shows': 2, u'theory': 13, u'G': 4, u'Schools': 1, u'List': 3, u'contemplation': 1, u'place': 3, u'511': 1, u'Hungary': 8, u'Eric': 1, u'frequent': 2, u'first': 3, u'surviving': 1, u'Yau': 1, u'There': 1, u'Royal': 3, u'one': 6, u'ErdosA.html': 1, u'Medicine': 1, u'open': 3, u'given': 2, u'Hoffman': 6, u'anyone': 2, u'2': 7, u'articles': 2, u'Date': 2, u'Post': 2, u'Data': 1, u'2008-09-29': 1, u'Giorgi': 1, u'mostly': 3, u'that': 20, u'PDF': 1, u'holder': 1, u'appreciated': 1, u'History': 1, u'11': 3, u'10': 4, u'13': 3, u'12': 3, u'15': 4, u'14': 5, u'17': 2, u'16': 2, u'19': 3, u'18': 3, u'r': 3, u'were': 14, u'and': 67, u'topics': 1, u'mater': 1, u'JSTOR': 1, u'Main': 1, u'saw': 1, u'any': 2, u'Eilenberg': 1, u'ideas': 1, u'Famous': 1, u'online': 1, u'wonder': 1, u'Hall': 2, u'200': 1, u'Name': 1, u'investigations': 1, u'keeps': 1, u'pair': 1, u'pages': 1, u'especially': 1, u'surprising': 1, u'considered': 2, u'later': 3, u'slaves': 1, u'Vojt': 1, u'typically': 2, u'quantity': 1, u'show': 1, u'Barry': 1, u'Political': 1, u'nther': 1, u'discovered': 1, u'Rolf': 1, u'Stephen': 1, u'radiolab': 1, u'Raman': 1, u'Shing-Tung': 1, u'3': 8, u'analytic': 1, u'only': 4, u'dispute': 1, u'stay': 1, u'get': 1, u'H': 1, u'Magazine': 1, u'framing': 1, u'BNF': 1, u'prime': 2, u'Searchable': 1, u'Selberg': 4, u'requesting': 1, u'Manchester': 2, u'where': 4, u'husband': 1, u'S0273-0979-08-01223-8': 1, u'physically': 1, u'concern': 1, u'That': 1, u'Fascist': 3, u'review': 2, u'Mikhail': 1, u'Berlin': 2, u'BOOK': 2, u'between': 2, u'reading': 1, u\"Wikipedia's\": 1, u'36575015': 1, u'Atheist': 1, u'style': 1, u'ascribed': 1, u'awards': 2, u'article': 5, u'concentrated': 1, u'22': 1, u'many': 5, u's': 120, u'among': 1, u'For.Mem.R.S': 1, u'Note': 1, u'Sciences': 1, u'62': 1, u'63': 1, u'66': 1, u'proved': 2, u'classic': 1, u'Perhaps': 2, u'Known': 1, u'500': 2, u'offered': 1, u'Endre': 1, u'careful': 1, u'calculus': 1, u'disconnected': 1, u'these': 2, u'policies': 1, u'Open': 3, u\"person's\": 1, u'conferences': 1, u'coffee': 1, u'Intelligencer': 1, u'drug': 1, u'GND': 1, u'Israel': 3, u'develop': 1, u'Notre': 2, u'same': 3, u'MaL': 1, u'Nationality': 1, u'11935003': 1, u'I': 5, u'Hell-Bound': 1, u'Physics': 1, u'tradition': 1, u'complained': 1, u'Is': 4, u'Kolmogorov': 1, u'It': 1, u'n50010022': 1, u'solve': 1, u'In': 9, u'scholarship': 1, u'United': 3, u'Service': 1, u'Prove': 1, u'being': 2, u'generally': 1, u'science.296.5565.39': 1, u'captured': 1, u'Centenary': 1, u'death': 5, u'thinking': 1, u'except': 1, u'4': 4, u'Although': 2, u'Israelis': 1, u'real': 1, u'around': 1, u'Phillip': 1, u'Project': 7, u'Benford': 1, u'perfect...You': 1, u'Nils': 1, u'world': 3, u'accepted': 1, u'recipient': 1, u'acute': 1, u'2013-03-26': 1, u'London': 1, u't': 2, u'fully': 1, u'output': 1, u'voluntarily': 1, u'Before': 1, u'Mark': 1, u'New': 7, u'prolific': 3, u'Men': 1, u'exit': 1, u'118994050': 1, u'NLA': 1, u'Artin': 1, u'scientific': 2, u'seconds': 1, u'notable': 1, u'1934': 1, u'1938': 1, u'Mathematical': 14, u'on': 10, u'of': 123, u'theorems': 6, u'favorite': 1, u'Scientist': 1, u'Lemonick': 1, u'stand': 1, u'or': 11, u'Story': 1, u'No': 1, u'references': 1, u'elementary': 2, u'your': 2, u'her': 2, u'removing': 1, u'there': 2, u'Shelah': 1, u'Calder': 1, u'Temet': 1, u'Letter': 1, u'passports': 1, u'enough': 1, u'J': 4, u'Smale': 1, u'Physical': 1, u'with': 21, u'Society': 6, u'suitcase': 1, u'Selfridge': 1, u'affection': 1, u'regimes': 1, u'strongly': 1, u'Paths': 1, u'diverges': 1, u'accents': 1, u'moved': 1, u'an': 19, u'as': 23, u'at': 19, u'lifetime': 3, u'film': 2, u'Golomb': 1, u'As': 2, u'Lab': 1, u'Lax': 2, u'Nathalie': 1, u'mathematics': 9, u'you': 3, u'thousand': 2, u'vocabulary': 2, u'academies': 1, u'students': 1, u'Fields': 3, u'time': 2, u'important': 1, u'included': 1, u'2009': 1, u'Brain': 2, u'doubted': 1, u'Melvin': 1, u'oral': 1, u'original': 1, u'external': 2, u'essay': 1, u'all': 7, u'Samuel': 1, u'month': 3, u'Theorem': 1, u'follow': 1, u'Moser': 1, u'children': 1, u'Euler': 2, u'collaborated': 1, u'tv': 1, u'to': 52, u'siblings': 1, u'Goffman': 3, u'far': 1, u'Wolf': 6, u\"I'm\": 3, u'Mostow': 1, u'list': 3, u'small': 2, u'titled': 1, u'lecturing': 1, u'192': 1, u'Only': 3, u'Interest': 1, u'further': 1, u'what': 3, u'sum': 2, u'scientists': 1, u'tribute': 1, u'method': 1, u'contrast': 1, u'5000': 1, u'ranged': 1, u'K': 1, u'Spencer': 4, u'Concept': 1, u'Griffiths': 1, u'inspired': 1, u'Ilya': 1, u'periodic': 1, u'social': 1, u'action': 1, u'Aug': 1, u'Rado': 1, u'contains': 4, u'two': 2, u'Baseball': 1, u'6': 4, u'hegemony': 1, u'more': 4, u'St': 2, u'American': 8, u'particular': 1, u'known': 1, u'town': 1, u'keeping': 1, u'Now': 1, u'Neumann': 1, u'KAPLANSKY': 1, u'remain': 2, u'v': 1, u'SF': 5, u'history': 1, u'beautiful': 1, u'states': 1, u'numbers': 5, u'Thompson': 1, u'biography': 2, u'archive': 1, u'earnings': 1, u'Fall': 1, u'1-85702-811-2': 1, u'derived': 1, u'617': 1, u'plane': 1, u'a': 61, u'Sweet': 1, u'SUDOC': 1, u'fundamental': 1, u'media': 1, u'infant': 1, u'help': 2, u\"don't\": 3, u'developed': 1, u'paper': 4, u'existence': 1, u'Finite': 1, u'its': 3, u'developer': 1, u'24': 1, u'25': 2, u'26': 6, u'27': 3, u'20': 8, u'21': 5, u'Stein': 1, u'23': 3, u'Stefan': 1, u'28': 3, u'29': 3, u'WorldCat': 1, u'colleague': 2, u'MacTutor': 1, u'Music': 1, u'Michael': 5, u'L': 4, u'Erd': 115, u'Goldfeld': 1, u'Chung': 3, u'mathematician': 3, u'always': 3, u'Authority': 1, u'stopped': 2, u'exiled': 1, u'found': 1, u'referred': 1, u'harm': 1, u'179': 1, u'Collatz': 1, u'Varadaraja': 1, u'ISNI': 1, u'Joseph': 3, u'since': 1, u'coauthor': 1, u'Mulcahy': 1, u'Leroy': 1, u'lord': 1, u'7': 6, u'denoted': 1, u'3-540-40460-0': 1, u'horse': 1, u'Historical': 1, u'ask': 1, u'curtailed': 1, u'unresolved': 1, u'People': 5, u'Dorian': 1, u'leading': 1, u'grossman': 1, u'probability': 2, u'number': 26, u'traveled': 1, u'solvers': 1, u'Faudree': 1, u'Sinai': 1, u'Personality': 2, u'story': 1, u'guest': 1, u'totally': 1, u'least': 3, u'Mathematician': 2, u'immediate': 1, u'Extremal': 1, u'part': 1, u'1913': 7, u'believe': 6, u'Andr': 4, u'Gowers': 1, u'albeit': 1, u'kind': 2, u'collaborations': 1, u'double': 1, u'Elementary': 1, u'traveling': 2, u'Doctoral': 2, u'outstanding': 2, u'footnote': 1, u'God': 9, u'Baas': 1, u'aged': 2, u'States': 2, u'pa': 1, u'also': 10, u're-entry': 1, u'Wayfarer': 1, u'Leopold': 2, u'Episode': 1, u'quote': 1, u'reach': 1, u'76': 1, u'significant': 1, u'70': 1, u'The': 25, u'probabilistic': 1, u'cb12371592h': 1, u'Google': 1, u'Wikimedia': 1, u'Straus': 1, u'If': 2, u'physics': 1, u'institutions': 1, u'particularly': 2, u'phenomenon': 1, u'journeys': 1, u'Hill': 1, u'Hajnal': 1, u'Kingdom': 1, u'parameters': 2, u'Lennart': 1, u'Zsolt': 1, u'failed': 1, u'Jo': 1, u'8': 4, u'Prime': 1, u'his': 39, u'Notes': 2, u'blank': 2, u'international': 1, u'during': 2, u'him': 5, u'Lecturing': 1, u'activity': 1, u'wrote': 2, u'set': 4, u'For': 3, u'see': 2, u'are': 5, u'2.2': 1, u'2.1': 1, u'Elected': 1, u'currently': 1, u'won': 3, u'various': 1, u'numerous': 1, u'both': 3, u'collaborators': 7, u'last': 1, u'rmander': 1, u'became': 2, u'posthumously': 1, u'Graham': 5, u'arbitrarily': 2, u'reasons': 1, u'Pomerance': 1, u'community': 1, u'throughout': 1, u'Rousseau': 1, u'pp': 2, u'Higginson': 1, u'described': 2, u'whom': 3, u'describes': 1, u'Carl': 2, u'collaborator': 2, u'extends': 1, u'treatment': 1, u'samland': 1, u'lived': 1, u'0000': 1, u'0001': 1, u'Princeton': 2, u'mind': 2, u'honorary': 3, u'great': 1, u'N': 5, u'0-684-84635-7': 1, u'doctorates': 1, u'Reddy': 1, u'Journeys': 2, u'while': 3, u'Colm': 1, u'replaced': 1, u'Cole': 1, u'styles': 1, u'vol': 1, u'imperialist': 1, u'Those': 1, u'commonly': 1, u'owes': 1, u'files.oakland.edu': 1, u'34': 1, u'Cite': 2, u'8511': 1, u'renounced': 1, u'Nation': 1, u'9': 2, u'development': 1, u'literature': 1, u'comprehensive': 1, u'000': 1, u'uses': 2, u'Publications': 1, u'necessity': 2, u'Wolffund.org.il': 1, u'early': 2, u'Soc': 1, u'spent': 1, u'analysis': 2, u'person': 2, u'entry': 1, u'Dennis': 1, u'intervals': 1, u'iUniverse': 1, u'Files': 1, u'Theory': 1, u'informal': 1, u'Emory': 1, u'parents': 3, u'Deligne': 1, u'Both': 1, u'Of': 1, u'Commons': 1, u'rsbm.1999.0011': 1, u'Langlands': 1, u'Truth': 1, u'2009-09-30': 1, u'Bott': 1, u'd': 3, u'Short': 1, u'Oakland.edu': 1, u'individuals': 1, u'mathematical': 14, u'often': 2, u'humorous': 1, u'some': 2, u'back': 2, u'2009-05-29': 1, u'Wiles': 1, u'5565': 1, u'Lajos': 1, u'AMS': 1, u'resolutely': 1, u'either': 2, u'be': 6, u'bb': 1, u'remembered': 1, u'M': 1, u'use': 2, u'David': 1, u'dictated': 1, u'by': 18, u'von': 1, u'integers': 1, u'Ron': 2, u'most': 11, u'in-depth': 1, u'Alfr': 3, u'progressions': 3, u'nder': 1, u'Simon': 2, u'71': 1, u'Hunters': 1, u'Approximately': 1, u'appropriate': 1, u'vagabond': 1, u'Zolt': 1, u'long': 5, u'himself': 7, u'Adrian': 1, u'Kolata': 1, u'Sergei': 1, u'Mumford': 1, u'Leray': 1, u'up': 3, u'Books': 1, u'Erdos': 11, u'Perspective': 1, u'called': 2, u'defined': 1, u\"article's\": 1, u'To': 2, u'engineering': 1, u'Bonifac': 1, u'lya': 1, u'Lecture': 1, u'1443': 1, u'denying': 1, u'Colorful': 1, u'Hillel': 1, u'A1': 1, u'application': 1, u'Tate': 1, u'gre': 1, u'actors': 1, u'Andrews': 2, u'Medal': 1, u'arithmetic': 3, u'Man': 3, u'elements': 1, u'users': 1, u'problems': 11, u'Documentary': 1, u'aesthetically': 1, u'independently': 1, u'e': 1, u'age': 4, u'An': 1, u'2002': 2, u'2003': 2, u'2000': 6, u'2001': 1, u'2006': 2, u'At': 2, u'2005': 3, u'2008': 4, u'Oakland': 1, u'having': 1, u'Warsaw': 3, u'Lars': 2, u'Monthly': 2, u'contributions': 2, u'Wittmeier': 1, u'Bondy': 1, u'Weil': 1, u'epitaph': 1, u'anti-communist': 1, u'include': 2, u'torture': 1, u'P': 5, u'Schechter': 3, u'Alcoholic': 1, u'Edmonton': 1, u'Related': 1, u'Skau': 1, u'smaller': 1, u\"Math's\": 1, u'video': 1, u'zy': 1, u'ardent': 1, u'Teaching': 1, u'universities': 1, u'Csicsery': 2, u'Laureates': 1, u'America': 1, u'can': 2, u'185310': 1, u'led': 2, u'degree': 2, u\"colleague's\": 1, u'jointly': 1, u'Greek': 1, u'Green': 1, u'separation': 1, u'fifteen': 1, u'PMID': 1, u'39': 2, u'38': 1, u'33': 1, u'32': 2, u'31': 1, u'30': 2, u'37': 1, u'36': 2, u'35': 3, u'Jean-Louis': 1, u'Radiolab': 1, u'649': 1, u'named': 2, u'heart': 1, u'win': 1, u'Robert': 1, u'Genius': 2, u'wit': 1, u'names': 1, u'Tits': 1, u'Notices': 1, u'J.J': 1, u'redi': 1, u'Draw': 1, u'Hassler': 1, u'from': 18, u'Siegel': 1, u'next': 2, u'few': 2, u'doubt': 2, u'Career': 2, u'prizes': 6, u'this': 5, u'Cited': 1, u'getting': 1, u'December': 1, u'Persondata': 1, u'proof': 4, u'control': 1, u'links': 5, u'high': 2, u'Yakov': 1, u'recognized': 1, u'Bounty': 1, u'Cultures': 1, u'www.wnyc.org': 1, u'Junkies': 1, u'winners': 1, u'profile': 1, u'Collaborators': 2, u'singular': 1, u'Joel': 4, u'them': 2, u'collection': 2, u'Carleson': 1, u'Portrait': 3, u'belongings': 1, u'light': 1, u'Szemer': 1, u'quotations': 1, u'discussion': 1, u'Aesthetic': 1, u'mathematicians': 7, u'including': 3, u'converting': 1, u'perfect': 2, u'la': 2, u'chosen': 1, u'Institutions': 1, u'degrees': 1, u'Luis': 1, u'2011': 3, u'2010': 2, u'2013': 2, u'2012': 3, u'Loved': 3, u'Tuza': 1, u'Raoul': 1, u'documented': 1, u'Creators': 1, u'day': 1, u'Summer': 1, u'Supreme': 4, u'renowned...are': 1, u'Sam': 1, u'profound': 1, u'edit': 12, u'Kunihiko': 1, u'Arts': 1, u'Statistics': 1, u'From': 2, u'doing': 1, u'administrator': 1, u'related': 2, u'88': 1, u'books': 1, u'83': 3, u'84': 1, u'out': 4, u'Conjecture': 1, u'Tur': 2, u'Vera': 2, u'may': 2, u'2009-10-09': 1, u'lecture': 1, u\"one's\": 1, u'1986': 2, u'Shortly': 1, u'This': 6, u'Henriksen': 1, u'1984': 1, u'promptly': 1, u'attending': 1, u'advisor': 3, u'implication': 1, u'resumed': 2, u'geometry': 1, u'deprecated': 2, u'could': 5, u'conversation': 1, u'length': 1, u'Reminiscences': 1, u\"Fascist-Erdos's\": 1, u'autographed': 1, u'Bollob': 2, u'awarded': 2, u'Wikiquote': 1, u'publication': 1, u'accent': 1, u'their': 4, u'attack': 2, u'Association': 1, u'Child': 1, u'R': 7, u'Krein': 1, u'Grossman': 6, u'colleagues': 1, u'References': 2, u'Casper': 2, u'doctorate': 2, u'Peter': 2, u'Revesz': 1, u'bet': 3, u'Caffarelli': 1, u'ISBN': 10, u'Richard': 3, u'0-684-85980-7': 2, u'Other': 2, u'have': 12, u'need': 1, u'Pal': 1, u'neater': 1, u'which': 5, u'Radio': 1, u'lecturer': 1, u'collaboration': 3, u'Chern': 1, u'visa': 1, u'eight': 1, u'Ernst': 1, u'Krauthammer': 1, u'why': 2, u'Some': 1, u'Nonbelievers': 1, u'looked': 1, u'Leonhard': 1, u'fact': 1, u'szl': 3, u'Religion': 1, u'pleased': 1, u'Math': 2, u'based': 1, u'credited': 1, u'should': 3, u'York': 6, u'meant': 1, u'rgen': 1, u'familiar': 2, u'Schelp': 1, u'joint': 1, u'words': 1, u'THE': 2, u'Because': 2, u'Sinclair': 1, u'Sullivan': 1, u'married': 2, u'contain': 1, u'Mikio': 1, u'Brent': 1, u'preach': 1, u'exists': 3, u'Source': 1, u'accused': 1, u'medalists': 1, u'packed': 1, u'pattern': 1, u'genius': 1, u'written': 3, u'Piranian': 1, u'July': 1, u'Jean-Pierre': 1, u'publishers': 1, u'comparable': 1, u'exam': 1, u'Novikov': 1, u'S': 3, u'exclaim': 1, u'piece': 2, u'career': 2, u'taking': 1, u'attributed': 1, u'Seminar': 1, u'Contents': 1, u'Timothy': 1, u'ch': 1, u'DVD': 1, u'Lor': 1, u'Coloring': 2, u'Lov': 1, u\"O'Connor\": 2, u'Immigration': 1, u'drank': 1, u'improve': 1, u'Ennio': 1, u'quotation': 1, u'And': 3, u'homes': 1, u'nd': 1, u'Number': 11, u'Nevanlinna': 1, u'almost': 1, u'site': 1, u'Mathematics': 15, u'You': 2, u'obituary': 1, u'perhaps': 2, u'began': 2, u'member': 1, u'joedom': 1, u'Prodigies': 1, u'difficult': 1, u'http': 1, u'Alma': 1, u'Purdue': 1, u'eccentric': 1, u'Reflections': 1, u'student': 2, u'infinite': 1, u'nation': 1, u'Order': 1, u'Chebyshev': 1, u'whole': 1, u'well': 2, u'Pierre': 1, u'thought': 2, u'354': 1, u'position': 1, u'excessive': 1, u'less': 1, u'42': 4, u'Fourth': 1, u'2317868': 2, u'web': 1, u'reciprocals': 1, u'mathematically': 2, u'other': 6, u'Fan': 3, u'citizen': 1, u'5': 6, u'1996-09-24': 1, u'1996-09-20': 1, u'978-0-387-74640-1': 1, u'government': 2, u'T': 1, u'Proof': 1, u'England': 1, u'vibrant': 1, u'works': 1, u'B8': 1, u'because': 3, u'classical': 2, u'sequence': 2, u'footage': 1, u'alive': 1, u'Mazur': 1, u'proofs': 8, u'Saharon': 1, u'Vladimir': 1, u'Mikl': 2, u'However': 1, u'does': 1, u'Bull': 1, u'bosses': 1, u'biology': 1, u'noise': 1, u'Baker': 1, u'G-d': 1, u'although': 2, u'worthy': 2, u'imaginary': 1, u'Chemistry': 1, u'Huffington': 1, u'hiding': 1, u'about': 3, u'lifestyle': 1, u'co-authors': 2, u'freedom': 2, u'abstinence': 1, u'US': 1, u'Cartan': 1, u'UK': 1, u'Japan': 1, u'tongue': 1, u'introduced': 1, u'documentary': 1, u'own': 5, u'Two': 1, u'socks': 1, u'three': 3, u'1956': 1, u'Kodaira': 1, u'Serre': 1, u'1987': 1, u'Gromov': 1, u'1985': 1, u'1982': 1, u'1983': 2, u'1980': 1, u'1981': 1, u'friends': 2, u'1988': 1, u'1989': 2, u'Ramsey': 1, u'ed': 1, u'November': 1, u'Science': 2, u'but': 5, u'highest': 1, u'he': 31, u'made': 1, u'Milnor': 1, u'whether': 1, u'official': 1, u'signed': 1, u'problem': 5, u'Women': 1, u'A25': 1, u'amphetamine': 1, u'Fellows': 1, u'Affinity': 1, u'education': 3, u'campus': 2, u'Lovasz': 1, u'48': 1, u'49': 1, u'46': 1, u'47': 1, u'44': 1, u'45': 4, u'percent': 1, u'43': 1, u'40': 2, u'41': 1, u'Volume': 1, u'book': 4, u'William': 1, u'March': 6, u'April': 2, u'else': 1, u'Shiing-Shen': 1, u'Page': 1, u'atheist': 3, u'in-cheek': 1, u'Atle': 3}", 
        "title": "Paul Erd\u0151s", 
        "url": "https://en.wikipedia.org/wiki/Paul_Erd%C5%91s", 
        "text": "Paul Erd\u0151s \n Paul Erd\u0151s at a student seminar in Budapest (Fall 1992) \n \n Born \n ( 1913-03-26 ) 26 March 1913 Budapest ,  Hungary \n Died \n 20 September 1996 ( 1996-09-20 )  (aged\u00a083) Warsaw ,  Poland \n Residence \n Hungary United Kingdom United States Israel \nThen itinerant \n Nationality \n Hungarian \n Fields \n Mathematics \n Institutions \n Manchester Princeton Purdue Notre Dame \nThen itinerant \n Alma mater \n E\u00f6tv\u00f6s Lor\u00e1nd University \n Doctoral advisor \n Leopold Fej\u00e9r \n Doctoral students \n Bonifac Donat Joseph Kruskal Alexander Soifer B\u00e9la Bollob\u00e1s [ 1 ] \n Known\u00a0for \n See list \n Notable awards \n Wolf Prize  (1983/84) AMS Cole Prize  (1951) \n Paul Erd\u0151s  ( Hungarian :  Erd\u0151s P\u00e1l   [\u02c8\u025brd\u00f8\u02d0\u0283 pa\u02d0l] ; 26 March 1913 \u2013 20 September 1996) was a  Hungarian   mathematician . Erd\u0151s worked with hundreds of collaborators, pursuing problems in  combinatorics ,  graph theory ,  number theory ,  classical analysis ,  approximation theory ,  set theory , and  probability theory . He was also known for his eccentric personality. [ 2 ] [ 3 ] \n \n \n \n Contents \n \n 1   Early life and education \n 2   Career \n 2.1   Mathematical work \n 2.2   Erd\u0151s' problems \n \n 3   Collaborators \n 4   Personality \n 5   Erd\u0151s number \n 6   See also \n 7   Notes \n 8   References \n 9   External links \n \n \n Early life and education [ edit ] \n Paul Erd\u0151s was born in  Budapest ,  Hungary , on March 26, 1913. [ 4 ]  He was the only surviving child of Anna and Lajos Erd\u0151s (formerly Engl\u00e4nder); [ 5 ]  his siblings died before he was born, aged 3 and 5. His parents were both mathematics teachers from a vibrant intellectual community. His fascination with mathematics  developed early \u2014at the age of four, he could calculate in his head how many seconds a person had lived, given their age. [ 6 ] \n \n Both of Erd\u0151s's parents were high school mathematics teachers, and Erd\u0151s received much of his early education from them. Erd\u0151s always remembered his parents with great affection. At 16, his father introduced him to two of his lifetime favorite subjects\u2014 infinite series  and  set theory . During high school, Erd\u0151s became an ardent solver of the problems proposed each month in  K\u00f6MaL , the Mathematical and Physical Monthly for Secondary Schools. [ 7 ] \n \n Erd\u0151s later published several articles in it about problems in elementary plane geometry. \n In 1934, at the age of 21, he was awarded a doctorate in mathematics. [ 8 ] \n Erd\u0151s's name contains the Hungarian letter \" \u0151 \" (\"o\" with  double acute accent ). This has led to many misspellings in the literature, typically  Erdos  or  Erd\u00f6s , either \"by mistake or out of typographical necessity\". [ 9 ] \n Career [ edit ] \n Because  anti-Semitism  was increasing in Hungary, he moved the same year he received his doctorate to  Manchester ,  England , to be a guest lecturer. In 1938, he accepted his first American position as a scholarship holder at  Princeton University . At this time, he began to develop the habit of traveling from campus to campus. He would not stay long in one place and traveled back and forth among mathematical institutions until his death. \n In 1952, during the  McCarthy anti-communist investigations , the U.S. government denied Erd\u0151s, a Hungarian citizen, a re-entry visa into the United States, for reasons that have never been fully explained. [ 10 ]  Teaching at  Notre Dame  at the time, Erd\u0151s could have chosen to remain in the country. Instead, he packed up and left, albeit requesting reconsideration from the  Immigration Service  at periodic intervals. The government changed its mind in 1963 and Erd\u0151s resumed including American universities in his teaching and travels. \n \n \n \n \nErd\u0151s,  Fan Chung , and her husband  Ronald Graham , Japan 1986 \n \n \n Hungary , then a  Communist  nation, was under the  hegemony  of the  Soviet Union . Although it curtailed the freedom of its citizens, in 1956 it gave Erd\u0151s the singular privilege of being allowed to enter and exit Hungary as he pleased. Erd\u0151s exiled himself voluntarily from Hungary in 1973 as a principled protest against his country's policy of denying entry to  Israelis . [ 11 ] \n During the last decades of his life, Erd\u0151s received at least fifteen honorary doctorates. He became a member of the scientific academies of eight countries, including the U.S.  National Academy of Sciences  and the UK  Royal Society . Shortly before his death, he renounced his honorary degree from the  University of Waterloo  over what he considered to be unfair treatment of colleague  Adrian Bondy . [ 12 ] [ 13 ]  On September 20, 1996, at the age of 83, he had a  heart attack  and died \"in action,\" attending a conference in  Warsaw . He never married and had no children. He is buried next to his mother and father in grave 17A-6-29 at  Kozma Utcai Temet\u0151  in  Budapest . [ 14 ] \n His life was documented in the film  N Is a Number: A Portrait of Paul Erd\u0151s , made while he was still alive, and posthumously in the book  The Man Who Loved Only Numbers  (1998). \n Mathematical work [ edit ] \n Erd\u0151s was one of the most prolific publishers of papers in mathematical history, comparable only with  Leonhard Euler ; Erd\u0151s published more papers, mostly in collaboration with other mathematicians, while Euler published more pages, mostly by himself. [ 15 ]  Erd\u0151s wrote around 1,525 mathematical articles in his lifetime, [ 16 ]  mostly with co-authors. He strongly believed in and practiced mathematics as a social activity, [ 17 ]  having 511 different collaborators in his lifetime. [ 18 ] \n In terms of mathematical style, Erd\u0151s was much more of a \"problem solver\" than a \"theory developer\". (See \"The Two Cultures of Mathematics\" [ 19 ]  by  Timothy Gowers  for an in-depth discussion of the two styles, and why problem solvers are perhaps less appreciated.)  Joel Spencer  states that \"his place in the 20th-century mathematical pantheon is a matter of some controversy because he resolutely concentrated on particular theorems and conjectures throughout his illustrious career.\" [ 20 ]  Erd\u0151s never won the highest mathematical prize, the  Fields Medal , nor did he coauthor a paper with anyone who did, [ 21 ]  a pattern that extends to other prizes. [ 22 ]  He did win the  Wolf Prize , where his contribution is described as \"for his numerous contributions to  number theory ,  combinatorics ,  probability ,  set theory  and  mathematical analysis , and for personally stimulating mathematicians the world over\". [ 23 ]  In contrast, the works of the three winners after were recognized as \"outstanding\", \"classic\", and \"profound\", and the three before as \"fundamental\" or \"seminal\". \n Of his contributions, the development of  Ramsey theory  and the application of the  probabilistic method  especially stand out.  Extremal combinatorics  owes to him a whole approach, derived in part from the tradition of  analytic number theory . Erd\u0151s found a proof for  Bertrand's postulate  which proved to be far neater than  Chebyshev 's original one. He also discovered an elementary proof for the  prime number theorem , along with  Atle Selberg . However, the circumstances leading up to the proofs, as well as publication disagreements, led to a bitter dispute between Erd\u0151s and Selberg. [ 24 ] [ 25 ]  Erd\u0151s also contributed to fields in which he had little real interest, such as topology, where he is credited as the first person to give an example of a  totally disconnected topological space  that is not  zero-dimensional . [ 26 ] \n Erd\u0151s' problems [ edit ] \n Throughout his career, Erd\u0151s would offer prizes for solutions to unresolved problems. [ 27 ]  These ranged from $25 for problems that he felt were just out of the reach of current mathematical thinking, to several thousand dollars for problems that were both difficult to attack and mathematically significant. There are thought to be at least a thousand such outstanding prizes, though there is no official or comprehensive list. The prizes remain active despite Erd\u0151s's death;  Ronald Graham  is the (informal) administrator of solutions. Winners can get either a check signed by Erd\u0151s (for framing only) or a cashable check from Graham. [ 28 ] \n Perhaps the most mathematically notable of these problems is the  Erd\u0151s conjecture on arithmetic progressions : \n If the sum of the reciprocals of a sequence of integers diverges, then the sequence contains  arithmetic progressions  of arbitrary length. \n If true, it would solve several other open problems in number theory (although one main implication of the conjecture, that the  prime numbers  contain arbitrarily long arithmetic progressions, has since been proved independently as the  Green\u2013Tao theorem ). The problem is currently worth US$5000. [ 29 ] \n The most familiar problem with an Erd\u0151s prize is likely the  Collatz conjecture , also called the 3 N \u00a0+\u00a01 problem. Erd\u0151s offered $500 for a solution. \n Collaborators [ edit ] \n His most frequent collaborators include Hungarian mathematicians  Andr\u00e1s S\u00e1rk\u00f6zy  (62 papers) and  Andr\u00e1s Hajnal  (56 papers), and American mathematician  Ralph Faudree  (50 papers). Other frequent collaborators were [ 30 ] \n \n B\u00e9la Bollob\u00e1s  (18 papers) \n Stefan Burr  (27 papers) \n Fan Chung  (14 papers) \n Zolt\u00e1n F\u00fcredi  (10 papers) \n Ron Graham  (28 papers) \n Andr\u00e1s Gy\u00e1rf\u00e1s  (15 papers) \n Richard R. Hall  (14 papers) \n Istv\u00e1n Jo\u00f3  (12 papers) \n Eric Milner  (15 papers) \n Melvyn Nathanson  (19 papers) \n Jean-Louis Nicolas  (19 papers) \n J\u00e1nos Pach  (21 papers) \n George Piranian  (14 papers) \n Carl Pomerance  (23 papers) \n Richard Rado  (18 papers) \n A. R. Reddy  (11 papers) \n Alfr\u00e9d R\u00e9nyi  (32 papers) \n Pal Revesz  (10 papers) \n Vojt\u011bch R\u00f6dl  (11 papers) \n C. C. Rousseau  (35 papers) \n Richard Schelp  (42 papers) \n John Selfridge  (14 papers) \n Mikl\u00f3s Simonovits  (21 papers) \n Vera S\u00f3s  (35 papers) \n Joel Spencer  (23 papers) \n Ernst G. Straus  (20 papers) \n Endre Szemer\u00e9di  (29 papers) \n Paul Tur\u00e1n  (30 papers) \n Zsolt Tuza  (12 papers) \n \n For other co-authors of Erd\u0151s, see the list of people with Erd\u0151s number 1 in  List of people by Erd\u0151s number . \n Personality [ edit ] \n \n \n \n Another roof, another proof. \n \n \n Paul Erd\u0151s [ 31 ] \n \n Possessions meant little to Erd\u0151s; most of his belongings would fit in a suitcase, as dictated by his itinerant lifestyle. Awards and other earnings were generally  donated  to people in need and various worthy causes. He spent most of his life as a  vagabond , traveling between scientific conferences and the homes of colleagues all over the world. He would typically show up at a colleague's doorstep and announce \"my brain is open\", staying long enough to collaborate on a few papers before moving on a few days later. In many cases, he would ask the current collaborator about whom to visit next. \n His colleague  Alfr\u00e9d R\u00e9nyi  said, \"a mathematician is a machine for turning  coffee  into  theorems \", [ 32 ]  and Erd\u0151s drank copious quantities. (This quotation is often attributed incorrectly to Erd\u0151s, [ 33 ]  but Erd\u0151s himself ascribed it to R\u00e9nyi. [ 34 ] ) After 1971 he also took  amphetamines , despite the concern of his friends, one of whom ( Ron Graham ) bet him $500 that he could not stop taking the drug for a month. [ 35 ]  Erd\u0151s won the bet, but complained that during his abstinence mathematics had been set back by a month: \"Before, when I looked at a piece of blank paper my mind was filled with ideas. Now all I see is a blank piece of paper.\" After he won the bet, he promptly resumed his amphetamine use. \n He had his own idiosyncratic vocabulary: Although an  atheist , [ 36 ] [ 37 ]  he spoke of \"The Book\", an imaginary book in which  God  had written down the best and most elegant proofs for mathematical theorems. [ 38 ]  Lecturing in 1985 he said, \"You don't have to believe in God, but you should believe in  The Book .\" He himself doubted the existence of God, whom he called the \"Supreme  Fascist \" (SF). [ 39 ] [ 40 ]  He accused the SF of hiding his socks and Hungarian  passports , and of keeping the most elegant mathematical proofs to himself. When he saw a particularly  beautiful mathematical proof  he would exclaim, \"This one's from  The Book !\". This later inspired a book entitled  Proofs from THE BOOK . \n Other idiosyncratic elements of Erd\u0151s's vocabulary include: [ 41 ] \n Children were referred to as \" epsilons \" (because in mathematics, particularly calculus, an arbitrarily small positive quantity is commonly denoted by the Greek letter (\u03b5)) \n Women were \"bosses\" \n Men were \"slaves\" \n People who stopped doing mathematics had \"died\" \n People who physically died had \"left\" \n Alcoholic drinks were \"poison\" \n Music (except classical music) was \"noise\" \n People who had married were \"captured\" \n People who had divorced were \"liberated\" \n To give a mathematical lecture was \"to preach\" \n To give an oral exam to a student was \"to torture\" him/her. \n Also, all countries which he thought failed to provide freedom to individuals as long as they did no harm to anyone else were classified as  imperialist  and given a name that began with a lowercase letter. For example, the  U.S.  was \"samland\" (after  Uncle Sam ), the Soviet Union was \"joedom\" (after  Joseph Stalin ), and  Israel  was \"isreal\". For his  epitaph  he suggested, \"I've finally stopped getting dumber.\" (Hungarian:  \"V\u00e9gre nem butulok tov\u00e1bb\" ). [ 42 ] \n Erd\u0151s number [ edit ] \n Main article:  Erd\u0151s number \n Because of his prolific output, friends created the  Erd\u0151s number  as a humorous tribute. An Erd\u0151s number describes a person's degree of separation from Erd\u0151s himself, based on their collaboration with him, or with another who has their own Erd\u0151s number. Erd\u0151s alone was assigned the Erd\u0151s number of 0 (for being himself), while his immediate collaborators could claim an Erd\u0151s number of 1, their collaborators have Erd\u0151s number at most 2, and so on. Approximately 200,000 mathematicians have an assigned Erd\u0151s number, [ 43 ]  and some have estimated that 90 percent of the world's active mathematicians have an Erd\u0151s number smaller than 8 (not surprising in light of the  small world phenomenon ). Due to collaborations with mathematicians, many scientists in fields such as physics, engineering, biology, and economics have Erd\u0151s numbers as well. [ 44 ] \n Jerry Grossman has written that it could be argued that  Baseball Hall of Famer   Hank Aaron  can be considered to have an Erd\u0151s number of 1 because they both autographed the same baseball when  Emory University  awarded them honorary degrees on the same day. [ 45 ]  Erd\u0151s numbers have also been proposed for an infant, a horse, and several actors. [ 46 ] \n The Erd\u0151s number was most likely first defined by Casper Goffman, [ 47 ]  an  analyst  whose own Erd\u0151s number is 2. [ 48 ]  Goffman published his observations about Erd\u0151s's prolific collaboration in a 1969 article titled \"And what is your Erd\u0151s number?\" [ 49 ] \n See also [ edit ] \n List of topics named after Paul Erd\u0151s \u00a0\u2013 including conjectures, numbers, prizes, and theorems \n Notes [ edit ] \n \n ^   \"Mathematics Genealogy Project\" . Retrieved 13 Aug 2012 . \u00a0 \n ^   Encyclop\u00e6dia Britannica article \n ^   Michael D. Lemonick (March 29, 1999).  \"Paul Erdos: The Oddball's Oddball\" . Time Magazine. \u00a0 \n ^   \"Erdos biography\" . Gap-system.org . Retrieved 2010-05-29 . \u00a0 \n ^   Baker, A.;  Bollobas, B.  (1999). \" Paul Erd\u0151s  26 March 1913 -- 20 September 1996: Elected For.Mem.R.S. 1989\".  Biographical Memoirs of Fellows of the Royal Society   45 : 147.  doi : 10.1098/rsbm.1999.0011 . \u00a0   edit \n ^   Hoffman, p. 66. \n ^   L\u00e1szl\u00f3 Babai.  \"Paul Erd\u0151s just left town\" . \u00a0 \n ^   Erd\u0151s's thesis advisor at the  University of Budapest  was Leopold Fej\u00e9r (or  Fej\u00e9r Lip\u00f3t ), who was also the thesis advisor for  John von Neumann ,  George P\u00f3lya , and  Paul (P\u00e1l) Tur\u00e1n . \n ^   The full quote is \"Note the pair of long accents on the \"\u0151,\" often (even in Erdos's own papers) by mistake or out of typographical necessity replaced by \"\u00f6,\" the more familiar German umlaut which also exists in Hungarian.\", from  Paul Erd\u0151s, D. Mikl\u00f3s, Vera T. S\u00f3s (1996).  Combinatorics, Paul Erd\u0151s is eighty . \u00a0 \n ^   \"Erdos biography\" . School of Mathematics and Statistics, University of St Andrews, Scotland. January 2000 . Retrieved 2008-11-11 . \u00a0   Cite uses deprecated parameters ( help ) \n ^   L\u00e1szl\u00f3 Babai and Joel Spencer.  \"Paul Erd\u0151s (1913\u20131996)\"  (PDF).  Notices of the American Mathematical Society  ( American Mathematical Society )  45  (1). \u00a0 \n ^   Letter  from Erd\u0151s to University of Waterloo \n ^   Transcription of October 2, 1996, article  from University of Waterloo Gazette \n ^   grave 17A-6-29 \n ^   Hoffman, p. 42. \n ^   Jerry Grossman.  \"Publications of Paul Erd\u00f6s\" . Retrieved 1 Feb 2011 . \u00a0 \n ^   Charles Krauthammer  (September 27, 1996).  \"Paul Erdos, Sweet Genius\" .  Washington Post . p.\u00a0A25. \u00a0   \"?\" . \u00a0 \n ^   \"The Erd\u0151s Number Project Data Files\" . Oakland.edu. 2009-05-29 . Retrieved 2010-05-29 . \u00a0 \n ^   This essay is in  Mathematics: Frontiers and Perspectives , Edited by V. I. Arnold, Michael Atiyah, Peter D. Lax and Barry Mazur, American Mathematical Society, 2000. Available online at  [1] . \n ^   Joel Spencer, \"Prove and Conjecture!\", a review of  Mathematics: Frontiers and Perspectives .  American Scientist , Volume 88, No. 6 November\u2013December 2000 \n ^   Paths to Erd\u00f6s \u2014 The Erd\u00f6s Number Project \n ^   From  \"trails to Erdos\" , by DeCastro and Grossman, in  The Mathematical Intelligencer , vol. 21, no. 3 (Summer 1999), 51\u201363: A careful reading of Table 3 shows that although Erdos never wrote jointly with any of the 42 [Fields] medalists (a fact perhaps worthy of further contemplation)... there are many other important international awards for mathematicians. Perhaps the three most renowned...are the Rolf Nevanlinna Prize, the Wolf Prize in Mathematics, and the Leroy P. Steele Prizes. ... Again, one may wonder why KAPLANSKY is the only recipient of any of these prizes who collaborated with Paul Erd\u00f6s. (After this paper was written, collaborator Lovasz received the Wolf prize, making 2 in all). \n ^   \"Wolf Foundation Mathematics Prize Page\" . Wolffund.org.il . Retrieved 2010-05-29 . \u00a0 \n ^   Goldfeld, Dorian (2003). \"The Elementary Proof of the Prime Number Theorem: an Historical Perspective\".  Number Theory: New York Seminar : 179\u2013192. \u00a0 \n ^   Baas, Nils A.; Skau, Christian F. (2008).  \"The lord of the numbers, Atle Selberg. On his life and mathematics\" .  Bull. Amer. Math. Soc.   45  (4): 617\u2013649.  doi : 10.1090/S0273-0979-08-01223-8 \u00a0 \n ^   Melvin Henriksen.  \"Reminiscences of Paul Erd\u00f6s (1913\u20131996)\" . Mathematical Association of America . Retrieved 2008-09-01 . \u00a0 \n ^   Brent Wittmeier, \"Math genius left unclaimed sum,\" Edmonton Journal, September 28, 2010.  [2] \n ^   Charles Seife (5 April 2002).  \"Erd\u00f6s's Hard-to-Win Prizes Still Draw Bounty Hunters\" .  Science   296  (5565): 39\u201340.  doi : 10.1126/science.296.5565.39 .  PMID \u00a0 11935003 . \u00a0 \n ^   p. 354, Soifer, Alexander (2008);  The Mathematical Coloring Book: Mathematics of Coloring and the Colorful Life of its Creators ; New York: Springer.  ISBN 978-0-387-74640-1 \n ^   List of collaborators of Erd\u0151s by number of joint papers , from the Erd\u0151s number project web site. \n ^   Cited in at least  20 books . \n ^   Biography of Alfr\u00e9d R\u00e9nyi  by J.J. O'Connor and E.F. Robertson \n ^   Bruno Schechter (2000),  My Brain is Open: The Mathematical Journeys of Paul Erd\u0151s , p.\u00a0155,  ISBN \u00a0 0-684-85980-7 \u00a0 \n ^   Paul Erd\u0151s (1995).  \"Child Prodigies\" .  Mathematics Competitions   8  (1): 7\u201315 . Retrieved July 17, 2012 . \u00a0 \n ^   Hill, J.  Paul Erdos, Mathematical Genius, Human (In That Order) \n ^   Colm Mulcahy (2013-03-26).  \"Centenary of Mathematician Paul Erd\u0151s -- Source of Bacon Number Concept\" . Huffington Post . Retrieved 13 April 2013 . \"In his own words, \"I'm not qualified to say whether or not God exists. I kind of doubt He does. Nevertheless, I'm always saying that the SF has this transfinite Book that contains the best proofs of all mathematical theorems, proofs that are elegant and perfect...You don't have to believe in God, but you should believe in the Book.\" (SF was his tongue- in-cheek reference to God as \"the Supreme Fascist\").\" \u00a0 \n ^   Jack Huberman (2008).  Quotable Atheist: Ammunition for Nonbelievers, Political Junkies, Gadflies, and Those Generally Hell-Bound . Nation Books. p.\u00a0107.  ISBN \u00a0 9781568584195 . \"I kind of doubt He [exists]. Nevertheless, I'm always saying that the SF [Supreme Fascist-Erdos's customary name for G-d has this transfinite Book ... that contains the best proofs of all theorems, proofs that are elegant and perfect.... You don't have to believe in God, but you should believe in the Book.\" \u00a0 \n ^   Nathalie Sinclair, William Higginson, ed. (2006).  Mathematics and the Aesthetic: New Approaches to an Ancient Affinity . Springer. p.\u00a036.  ISBN \u00a0 9780387305264 . \"Erd\u00f6s, an atheist, named 'the Book' the place where God keeps aesthetically perfect proofs.\" \u00a0 \n ^   Schechter, Bruce (2000).  My brain is open: The mathematical journeys of Paul Erd\u0151s . New York:  Simon & Schuster . pp.\u00a070\u201371.  ISBN \u00a0 0-684-85980-7 . \u00a0 \n ^   Varadaraja Raman (2005).  Variety in Religion And Science: Daily Reflections . iUniverse. p.\u00a0256.  ISBN \u00a0 9780595358403 . \"Erd\u00f6s had a pungent wit. As an atheist who had suffered under fascist regimes, he described God as a Supreme Fascist.\" \u00a0 \n ^   Hoffman, chapter 1.  As included with the New York Times review of the book . \n ^   Hoffman, p. 3. \n ^   \"From Benford to Erd\u00f6s\" .  Radio Lab . Episode 2009-10-09. 2009-09-30 .  http://www.wnyc.org/shows/radiolab/episodes/2009/10/09/segments/137643 . \n ^   Jerry Grossman.  \"Some Famous People with Finite Erd\u00f6s Numbers\" . Retrieved 1 Feb 2011 . \u00a0 \n ^   Jerry Grossman.  \"Items of Interest Related to Erd\u00f6s Numbers\" . \u00a0 \n ^   Extended Erd\u0151s Number Project \n ^   Michael Golomb 's  obituary of Paul Erd\u0151s \n ^   https://files.oakland.edu/users/grossman/enp/ErdosA.html  from the Erdos Number Project \n ^   Goffman, Casper (1969). \"And what is your Erd\u0151s number?\".  American Mathematical Monthly   76  (7): 791.  doi : 10.2307/2317868 .  JSTOR \u00a0 2317868 . \u00a0 \n \n References [ edit ] \n Aigner, Martin ; G\u00fcnther Ziegler (2003).  Proofs from THE BOOK . Berlin; New York: Springer.  ISBN \u00a0 3-540-40460-0 . \u00a0   Cite uses deprecated parameters ( help ) \n Csicsery, George Paul (2005).  N Is a Number: A Portrait of Paul Erd\u0151s . Berlin; Heidelberg: Springer Verlag.  ISBN \u00a0 3-540-22469-6 . \u00a0  - DVD\n 1993 documentary film  \"N Is a Number: A Portrait of Paul Erd\u0151s\"  by George Paul Csicsery. \n \n Hoffman, Paul  (1998).  The Man Who Loved Only Numbers : The Story of Paul Erd\u0151s and the Search for Mathematical Truth . London: Fourth Estate Ltd.  ISBN \u00a0 1-85702-811-2 . \u00a0 \n Kolata, Gina (1996-09-24).  \"Paul Erdos, 83, a Wayfarer In Math's Vanguard, Is Dead\" .  New York Times . pp.\u00a0A1 and B8 . Retrieved 2008-09-29 . \u00a0 \n Bruce Schechter (1998).  My Brain is Open: The Mathematical Journeys of Paul Erd\u0151s . Simon & Schuster.  ISBN \u00a0 0-684-84635-7 . \u00a0 \n External links [ edit ] \n \n \n \n This article's  use of  external links  may not follow Wikipedia's policies or guidelines .  Please  improve this article  by removing  excessive  or  inappropriate  external links, and converting useful links where appropriate into  footnote references .   (September 2011) \n \n Wikiquote has a collection of quotations related to:  Paul Erd\u0151s \n \n Wikimedia Commons has media related to  Paul Erd\u0151s . \n Erd\u0151s's Scholar Google profile \n Searchable collection of (almost) all papers of Erd\u0151s \n O'Connor, John J. ;  Robertson, Edmund F. ,  \"Paul Erd\u0151s\" ,  MacTutor History of Mathematics archive ,  University of St Andrews \u00a0 . \n Paul Erd\u0151s  at the  Mathematics Genealogy Project \n Jerry Grossman at Oakland University.  The Erd\u00f6s Number Project \n The Man Who Loved Only Numbers  - Royal Society Public Lecture by Paul Hoffman (video) \n Paul Erd\u00f6s: N is a number  - (Documentary) Contains footage of Erd\u00f6s lecturing and in conversation. \n Radiolab: Numbers, with a story on Paul Erd\u0151s \n Fan Chung, \"Open problems of Paul Erd\u0151s in graph theory\" \n \n \n \n v \n t \n e \n \n Laureates of the  Wolf Prize in Mathematics \n \n \n \n \n Israel Gelfand  /  Carl L. Siegel  (1978) \n Jean Leray  /  Andr\u00e9 Weil  (1979) \n Henri Cartan  /  Andrey Kolmogorov  (1980) \n Lars Ahlfors  /  Oscar Zariski  (1981) \n Hassler Whitney  /  Mark Krein  (1982) \n Shiing-Shen Chern  /  Paul Erd\u0151s  (1983/4) \n Kunihiko Kodaira  /  Hans Lewy  (1984/5) \n Samuel Eilenberg  /  Atle Selberg  (1986) \n Kiyoshi It\u014d  /  Peter Lax  (1987) \n Friedrich Hirzebruch  /  Lars H\u00f6rmander  (1988) \n Alberto Calder\u00f3n  /  John Milnor  (1989) \n Ennio de Giorgi  /  Ilya Piatetski-Shapiro  (1990) \n Lennart Carleson  /  John G. Thompson  (1992) \n Mikhail Gromov  /  Jacques Tits  (1993) \n J\u00fcrgen Moser  (1994/5) \n Robert Langlands  /  Andrew Wiles  (1995/6) \n Joseph Keller  /  Yakov G. Sinai  (1996/7) \n L\u00e1szl\u00f3 Lov\u00e1sz  /  Elias M. Stein  (1999) \n Raoul Bott  /  Jean-Pierre Serre  (2000) \n Vladimir Arnold  /  Saharon Shelah  (2001) \n Mikio Sato  /  John Tate  (2002/3) \n Grigory Margulis  /  Sergei Novikov  (2005) \n Stephen Smale  /  Hillel Furstenberg  (2006/7) \n Pierre Deligne  /  Phillip A. Griffiths  /  David B. Mumford  (2008) \n Dennis Sullivan  /  Shing-Tung Yau  (2010) \n Michael Aschbacher  /  Luis Caffarelli  (2012) \n George Mostow  /  Michael Artin  (2013) \n \n \n \n \n \n Agriculture \n Arts \n Chemistry \n Mathematics \n Medicine \n Physics \n \n \n \n \n Authority control \n \n \n WorldCat \n VIAF :  51768730 \n LCCN :  n50010022 \n ISNI :  0000 0001 1443 8511 \n GND :  118994050 \n LIBRIS :  185310 \n SUDOC :  050328956 \n BNF :  cb12371592h \n NLA :  36575015 \n \n \n \n \n Persondata \n Name \n Erd\u0151s, Paul \n Alternative names \n Erdos, Paul (Anglicization); Erd\u0151s P\u00e1l (Birth name) \n Short description \n Mathematician \n Date of birth \n March 26, 1913 \n Place of birth \n Budapest ,  Hungary \n Date of death \n September 20, 1996 \n Place of death \n Warsaw ,  Poland \n", 
        "abstract": "", 
        "modified": "2013-12-28T08:00:00Z", 
        "crawled": "2014-01-15T12:23:18Z", 
        "toc": "1 Early life and education 2 Career 2.1 Mathematical work 2.2 Erd\u0151s' problems  3 Collaborators 4 Personality 5 Erd\u0151s number 6 See also 7 Notes 8 References 9 External links ", 
        "crawler": "wiki"
        }
    }"""


def django_object_from_row(row, model, field_names=None, include_id=False, strip=True, verbosity=0):
    return model(**field_dict_from_row(row, model, field_names=field_names, include_id=include_id, strip=strip, verbosity=verbosity))


def field_dict_from_row(row, model, field_names=None, include_id=False, strip=True, verbosity=0):
    field_classes = [f for f in model._meta._fields() if (include_id or f.name != 'id')]
    if not field_names:
        field_names = [f.name for f in field_classes if (include_id or f.name != 'id')]
    field_dict = {}
    if isinstance(row, Mapping):
        row = [row.get(field_name, '') for field_name in field_names]
    for field_name, field_class, value in zip(field_names, field_classes, row):
        if verbosity >= 3:
            print field_name, field_class, value 
        if not value:
            value = None

        try:
            # get a clean python value from a string, etc
            clean_value = field_class.to_python(value)
        except:  # ValidationError
            try:
                clean_value = str(field_class.to_python(util.clean_wiki_datetime(value)))
            except:
                clean_value = field_class().to_python()
        if isinstance(clean_value, basestring):
            if strip:
                clean_value = clean_value.strip()
            clean_value = clean_utf8(clean_value)
        field_dict[field_name] = clean_value
    return field_dict


def load_csv_to_model(path, model, field_names=None, delimiter='|', batch_size=1000, num_header_rows=1, strip=True, dry_run=True, verbosity=1):
    """Bulk create databse records from batches of rows in a csv file."""
    path = path or './'
    if not delimiter:
        for d in ',', '|', '\t', ';':
            try:
                return load_csv_to_model(path=path, model=model, field_names=field_names, delimiter=d, batch_size=batch_size, num_header_rows=num_header_rows, strip=strip, dry_run=dry_run, verbosity=verbosity)
            except:
                pass
        return None
    delimiter = str(delimiter)
    with open(path, 'rb') as f:
        reader = csv.reader(f, dialect='excel', delimiter=delimiter)
        header_rows = []
        for i in range(num_header_rows):
            header_rows += [reader.next()]
        i = 0
        for batch_num, batch_of_rows in enumerate(util.generate_batches(reader, batch_size)):
            i += len(batch_of_rows)
            if verbosity:
                print i
            batch_of_objects = [django_object_from_row(row, model=model, field_names=field_names, strip=strip) for row in batch_of_rows]
            if not dry_run:
                model.objects.bulk_create(batch_of_objects)
            elif verbosity:
                print "DRY_RUN: NOT bulk creating batch of %d records in %r" % (len(batch_of_objects), model)
    return i


def load_all_csvs_to_model(path, model, field_names=None, delimiter=None, batch_size=10000, num_header_rows=1, recursive=False, clear=False, dry_run=True, strip=True, verbosity=1):
    """Bulk create database records from all csv files found within a directory."""
    path = path or './'
    batch_size = batch_size or 1000
    if verbosity:
        if dry_run:
            print 'DRY_RUN: actions will not modify the database.'
        else:
            print 'THIS IS NOT A DRY RUN, THESE ACTIONS WILL MODIFY THE DATABASE!!!!!!!!!'
    if clear:
        ans = 'y'
        if verbosity and not dry_run:
            ans = input('Are you sure you want to delete all %d existing database records in %r? (y/n)' % (model.objects.all().count(), model))
        if ans.lower().startswith('y') and not dry_run:
            model.objects.all().delete()
        if dry_run:
            print "DRY_RUN: NOT deleting %d records in %r." % (model.objects.all().count(), model)
    N = 0
    for dir_path, dir_names, filenames in os.walk(path):
        if verbosity:
            print dir_path, dir_names, filenames
        for fn in filenames:
            if verbosity:
                print 'loading "%s"...' % os.path.join(dir_path, fn)
            if fn.lower().endswith(".csv"):
                N += load_csv_to_model(path=os.path.join(dir_path, fn), model=model, field_names=field_names, delimiter=delimiter, strip=strip, batch_size=batch_size, num_header_rows=num_header_rows, dry_run=dry_run, verbosity=verbosity)
        if not recursive:
            return N
    return N


def clean_duplicates(model, unique_together=('material', 'serial_number',), date_field='created_on',
                     seq_field='model_serial_seq', seq_max_field='model_serial_seq_max', verbosity=1):
    qs = model.objects.order_by(list(unique_together) + util.listify(date_field)).all()
    N = qs.count()

    if verbosity:
        print 'Retrieving the first of %d records for %r.' % (N, model)
    qsit = iter(qs)
    i, obj = 1, qsit.next()
    setattr(obj, seq_field, 0)
    setattr(obj, seq_max_field, 0)
    obj.save()
    dupes = [obj]

    if verbosity:
        widgets = ['%d rows: ' % N, Percentage(), ' ', RotatingMarker(), ' ', Bar(),' ', ETA()]
        i, pbar = 0, ProgressBar(widgets=widgets, maxval=N).start()       
    for obj in qsit:
        if verbosity:
            pbar.update(i)
        i += 1
        if all([getattr(obj, f, None) == getattr(dupes[0], f, None) for f in unique_together]):
            dupes += [obj]
        else:
            if len(dupes) > 1:
                for j in range(len(dupes)):
                    setattr(dupes[j], seq_field, j)
                    setattr(dupes[j], seq_max_field, len(dupes) - 1)
                    dupes[j].save() 
                # model.bulk_create(dupes) would not delete the old ones, would have to do that separately
                # model.bulk_create(dupes)
            dupes = [obj]
    if verbosity:
        pbar.finish()


def import_items(item_seq, dest_model,  batch_size=500, clear=False, dry_run=True, verbosity=1):
    """Given a sequence (queryset, generator, tuple, list) of dicts import them into the given model"""
    try:
        try:
            src_qs = item_seq.objects.all()
        except:
            src_qs = item_seq.all()
        N = src_qs.count()
        item_seq = iter(src_qs.values())
    except:
        print_exc()
        N = len(item_seq)

    if verbosity:
        print('Loading %r records from sequence provided...' % N)
        widgets = ['%d records: ' % N, Percentage(), ' ', RotatingMarker(), ' ', Bar(),' ', ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=N).start()

    if clear and not dry_run:
        if verbosity:
            print "WARNING: Deleting %d records from %r !!!!!!!" % (dest_model.objects.count(), dest_model)
        dest_model.objects.all().delete()
    for batch_num, dict_batch in enumerate(util.generate_batches(item_seq, batch_size)):
        if verbosity > 2:
            print(repr(dict_batch))
            print(repr((batch_num, len(dict_batch), batch_size)))
            print(type(dict_batch))
        item_batch = []
        for d in dict_batch:
            if verbosity > 2:
                print(repr(d))
            m = dest_model()
            try:
                m.import_item(d, verbosity=verbosity)
            except:
                m = django_object_from_row(d, dest_model)
            item_batch += [m]
        if verbosity and verbosity < 2:
            pbar.update(batch_num * batch_size + len(dict_batch))
        elif verbosity > 1:
            print('Writing {0} items in batch {2} out of {3} batches to the {4} model...'.format(
                len(item_batch), batch_num, int(N / float(batch_size)), dest_model))
        if not dry_run:
            dest_model.objects.bulk_create(item_batch)
    if verbosity:
        pbar.finish()


def import_queryset(qs, dest_model,  batch_size=500, clear=False, dry_run=True, verbosity=1):
    """Given a sequence (queryset, generator, tuple, list) of dicts import them into the given model"""
    try:
        qs = qs.objects
    except:
        pass
    N = qs.count()

    if verbosity:
        print('Loading %r records from the queryset provided...' % N)
    qs = qs.values()

    if clear and not dry_run:
        if verbosity:
            print "WARNING: Deleting %d records from %r !!!!!!!" % (dest_model.objects.count(), dest_model)
        dest_model.objects.all().delete()
    if verbosity:
        widgets = ['%d records: ' % N, Percentage(), ' ', RotatingMarker(), ' ', Bar(),' ', ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=N).start()
    for batch_num, dict_batch in enumerate(util.generate_batches(qs, batch_size)):
        if verbosity > 2:
            print(repr(dict_batch))
        item_batch = []
        for d in dict_batch:
            if verbosity > 2:
                print(repr(d))
            m = dest_model()
            try:
                m.import_item(d, verbosity=verbosity)
            except:
                m = django_object_from_row(d, dest_model)
            item_batch += [m]
        if verbosity and verbosity < 2:
            pbar.update(batch_num * batch_size + len(dict_batch))
        elif verbosity > 1:
            print('Writing {0} items in batch {2} out of {3} batches to the {4} model...'.format(
                len(item_batch), batch_num, int(N / float(batch_size)), dest_model))
        if not dry_run:
            dest_model.objects.bulk_create(item_batch)
    if verbosity:
        pbar.finish()
# def import_qs(src_qs, dest_model,  batch_size=100, db_alias='default', 
#         unique_together=('model', 'serialno'), seq_field='model_serial_seq', seq_max_field='model_serial_seq_max', 
#         verbosity=2):
#     """FIXME: Given a sequence (queryset, generator, tuple, list) of dicts import them into the given model

#     Efficiently count duplicates of the index formed from the fields listed in unique_together.
#     Store this count in the new model in the field indicated by the `seq_max_field` argument.
#     Store a sequence number in `seq_field`, starting at 0 and ending at the value stored in `seq_max_field`
#     """
#     num_items = None
#     src_qs = None
#     try:
#         src_qs = src_qs.objects.all()
#     except:
#         src_qs = src_qs.all()

#     index_uniques = False
#     if index_uniques and hasattr(dest_model, seq_field) and hasattr(dest_model, seq_max_field):
#         try:
#             src_qs = src_qs.order_by(*unique_together)
#             index_uniques = True
#         except:
#             print_exc()

#     try:
#         item_seq = src_qs.values()
#     except:
#         print_exc()

#     num_items = src_qs.count()

#     if verbosity > 1:
#         print('Loading %r records from seq provided...' % num_items)
#     dupes = []
#     for batch_num, dict_batch in enumerate(util.generate_batches(item_seq, batch_size)):
#         if verbosity > 2:
#             print(repr(dict_batch))
#             print(repr((batch_num, len(dict_batch), batch_size)))
#             print(type(dict_batch))
#         item_batch = []
#         for d in dict_batch:
#             if verbosity > 2:
#                 print(repr(d))
#             m = dest_model()
#             try:
#                 m.import_item(d, verbosity=verbosity)
#             except:
#                 m = django_object_from_row(d, dest_model)
#             if index_uniques:
#                 if dupes:
#                     try:
#                         if all([getattr(dupes[0], f) == getattr(m, f) for f in unique_together]):
#                             setattr(m, seq_field, getattr(dupes[-1], seq_field) + 1)
#                             dupes += [m]
#                         else:
#                             for j in range(len(dupes)):
#                                 setattr(dupes[j], seq_max_field, len(dupes) - 1) 
#                             dupes = [m]
#                     except:
#                         pass # FIXME
#                 else:
#                     dupes = [m]

#             item_batch += [m]
#         if verbosity > 1:
#             print('Writing {0} {1} items in batch {2} out of {3} batches to the {4} database...'.format(
#                 len(item_batch), dest_model.__name__, batch_num, int(num_items / float(batch_size)), db_alias))
#         dest_model.objects.bulk_create(item_batch)

def import_json(path, model, batch_size=100, db_alias='default', verbosity=2):
    """Read json file (not in django fixture format) and create the appropriate records using the provided database model."""

    # TODO: use a generator to save memory for large json files/databases
    if verbosity:
        print('Reading json records (dictionaries) from {0}.'.format(repr(path)))
    item_list = json.load(open(path, 'r'))
    if verbosity:
        print('Finished reading {0} items from {1}.'.format(len(item_list), repr(path)))
    import_items(item_list, model=model, batch_size=batch_size, db_alias=db_alias, verbosity=verbosity)


def fixture_from_table(table, header_rows=1):
    """JSON string that represents a valid Django fixture for the data in a table"""
    yield '[\n'
    for i in range(header_rows, len(table)):
        s = fixture_record_from_row(table[i])
        if i == header_rows:
            yield s + '\n'
        else:
            yield ',\n' + s + '\n'
    yield ']\n'