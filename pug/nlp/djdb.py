
import datetime
from collections import OrderedDict, Mapping
import re
from types import ModuleType
import sqlparse

from fuzzywuzzy import process as fuzzy
import numpy as np
import logging
logger = logging.getLogger('bigdata.info')


DEFAULT_APP = None  # models.get_apps()[-1]
DEFAULT_MODEL = None  # DEFAULT_MODEL.get_models()[0]
from django.core.exceptions import ImproperlyConfigured
try:
    from django.db import models, connection
except ImproperlyConfigured:
    import traceback
    print traceback.format_exc()
    print 'WARNING: The module named %r from file %r' % (__name__, __file__)
    print '         can only be used within a Django project!'
    print '         Though the module was imported, some of its functions may raise exceptions.'

import util  # import transposed_lists #, sod_transposed
from .words import synonyms
from .util import listify
from .db import sort_prefix, consolidated_counts, sorted_dict_of_lists, lagged_seq, NULL_VALUES, NAN_VALUES, BLANK_VALUES


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
def normalize_choices(db_values, app_module, field_name, model_name='', human_readable=True, none_value='Null', blank_value='Unknown', missing_value='Unknown DB Code'):
    if isinstance(app_module, basestring):
        app_module = get_app(app_module)
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
            if db_value in (None, 'None'):
                db_values[field_name][i] = none_value
                continue
            if isinstance(db_value, basestring):
                normalized_code = str(db_value).strip().upper()
            choices = getattr(app_module.models, 'CHOICES_%s' % field_name.upper())
            normalized_name = None
            if choices:
                normalized_name = str(choices.get(normalized_code, missing_value)).strip()
            elif normalized_code:
                normalized_name = 'DB Code: "%s"' % normalized_code
            db_values[field_name][i] = normalized_name or blank_value
    else:
        raise NotImplemented("This function can only convert database choices to human-readable strings.")
    return db_values


def get_app(app=-1):
    """
    >>> get_app('call').__class__.__name__ == 'module'
    True
    >>> get_app('cal cent').__name__ == 'miner.models'
    True
    >>> isinstance(get_app('whatever'), ModuleType)
    True
    """
    if app is -1:
        app = get_app.default
    if isinstance(app, ModuleType):
        return app
    try:
        return models.get_app(app)
    except:
        pass
    if app:
        app_names = [app_class.__package__ for app_class in models.get_apps()]
        return models.get_app(fuzzy.extractOne(str(app), app_names)[0])
    return [app_class.__package__ for app_class in models.get_apps()]
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
    if isinstance(model, models.base.ModelBase):
        return model
    model_name = None
    try:
        model_name = models.get_model(app, model) 
    except:
        pass
    if model_name:
        return model_name
    app = get_app(app)
    model_names = [mc.__name__ for mc in models.get_models(app)]
    return models.get_model(app.__package__.split('.')[-1], fuzzy.extractOne(str(model), model_names)[0])




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
    objects = normalize_choices(util.sod_transposed(objects), app_module=app, field_name=x, human_readable=True)
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
