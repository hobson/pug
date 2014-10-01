#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Django database manipulations (using the ORM) that require the settings module to be imported"""

import datetime
import collections
import re
from types import ModuleType
import sqlparse
import os
import csv
import json
import warnings
from traceback import print_exc
from copy import deepcopy
from decimal import Decimal
from operator import itemgetter
from types import NoneType
import importlib

from django.core import serializers
from django.db.models import related
from django.db import transaction
from django.db import models as djmodels

import progressbar as pb  # import ProgressBar, Percentage, RotatingMarker, Bar, ETA
from fuzzywuzzy import process as fuzzy
import numpy as np
import logging
logger = logging.getLogger('bigdata.info')

from dateutil.parser import parse as parse_date

# required to monkey-patch django.utils.encoding.force_text
from django.utils.encoding import is_protected_type, DjangoUnicodeDecodeError, six
DEFAULT_DB = 'default'
DEFAULT_APP = None  # djmodels.get_apps()[-1]
DEFAULT_MODEL = None  # DEFAULT_MODEL.get_models()[0]
from django.core.exceptions import ImproperlyConfigured
settings = None
try:
    # FIXME Only 1 function that requires settings: all other functions should be moved to nlp.db module?
    from django.conf import settings  
except ImproperlyConfigured:
    print print_exc()
    print 'WARNING: The module named %r from file %r' % (__name__, __file__)
    print '         can only be used within a Django project!'
    print '         Though the module was imported, some of its functions may raise exceptions.'


from pug.nlp import util  # import listify, generate_slices, transposed_lists #, sod_transposed, dos_from_table
from pug.nlp.words import synonyms
from pug.nlp.db import sort_prefix, consolidated_counts, sorted_dict_of_lists, clean_utf8, replace_nonascii, lagged_seq, NULL_VALUES, NAN_VALUES, BLANK_VALUES
from pug.miner.models import ChangeLog


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


def normalize_values_queryset(values_queryset, model=None, app=None, verbosity=1):
    '''Shoehorn the values from one database table into another

    * Remove padding (leading/trailing spaces) from `CharField` and `TextField` values
    * Truncate all `CharField`s to the max_length of the destination `model`
    * Subsititue blanks ('') for any None values destined for `null=False` fields

    Returns a list of unsaved Model objects rather than a queryset
    '''
    model = model or values_queryset.model
    app = app or DEFAULT_APP
    new_list = []
    for record in values_queryset:
        new_record = {}
        for k, v in record.iteritems():
            field_name = find_field(k, model=model, app=app)
            field_class = model._meta.get_field(field_name)
            # if isinstance(field_class, (djmodels.fields.DateTimeField, djmodels.fields.DateField)):
            #     new_record[field_name] = unix_timestamp(v)
            # try:
            if isinstance(field_class, (djmodels.fields.CharField, djmodels.fields.TextField))  or isinstance(v, basestring):
                if v is None:
                    v = ''
                else:
                    v = unicode(v).strip()
            if isinstance(field_class, djmodels.fields.CharField):
                if len(v) > getattr(field_class, 'max_length', 0):
                    if verbosity:
                        print k, v, len(v), '>', field_class.max_length
                        print 'string = %s' % repr(v)
                    # truncate strings that are too long for the database field
                    v = v[:getattr(field_class, 'max_length', 0)]
            new_record[field_name] = v
            # except:
            #     pass
            if (v is None or new_record[field_name] is None) and not getattr(field_class, 'null'):
                new_record[field_name] = ''
        if verbosity > 1:
            print new_record
        new_list += [new_record]
    return new_list


def make_choices(*args):
    """Convert a 1-D sequence into a 2-D sequence of tuples for use in a Django field choices attribute

    >>> make_choices(range(3))
    ((0, u'0'), (1, u'1'), (2, u'2'))
    >>> make_choices(dict(enumerate('abcd')))
    ((0, u'a'), (1, u'b'), (2, u'c'), (3, u'd'))
    >>> make_choices('hello')
    (('hello', u'hello'),)
    >>> make_choices('hello', 'world') == make_choices(['hello', 'world']) == (('hello', u'hello'), ('world', u'world'))
    True
    """
    if not args:
        return tuple()
    if isinstance(args[0], (list, tuple)):
        return make_choices(*tuple(args[0]))
    elif isinstance(args[0], collections.Mapping):
        return tuple((k, unicode(v)) for (k, v) in args[0].iteritems())
    elif all(isinstance(arg, (int, float, Decimal, basestring)) for arg in args):
        return tuple((k, unicode(k)) for k in args)


# TODO: use both get and set to avoid errors when different values chosen
# TODO: modularize in separate function that finds CHOICES appropriate to a value key
def normalize_choices(db_values, field_name, app=DEFAULT_APP, model_name='', human_readable=True, none_value='Null', 
                      blank_value='Unknown', missing_value='Unknown DB Code'):
    '''Output the human-readable strings associated with the list of database values for a model field.

    Uses the translation dictionary `CHOICES_<FIELD_NAME>` attribute for the given `model_name`.
    In addition, translate `None` into 'Null', or whatever string is indicated by `none_value`.
    '''
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
    """Uses django.db.djmodels.get_app and fuzzywuzzy to get the models module for a django app

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
            return [app_class.__package__ for app_class in djmodels.get_apps() if app_class and app_class.__package__]
        # for a blank string, get the default app(s)
        else:
            if get_app.default:
                return get_app(get_app.default)
            else:
                return djmodels.get_apps()[-1]
    elif isinstance(app, ModuleType):
        return app
    elif isinstance(app, basestring):
        if app.strip().endswith('.models'):
            return get_app(app[:-len('.models')])
        elif '.' in app:
            return get_app('.'.join(app.split('.')[1:]))  # django.db.models only looks at the module name in the INSTALLED_APPS list!         
    try:
        if verbosity > 1:
            print 'Attempting django.db.models.get_app(%r)' % app
        return djmodels.get_app(app)
    except ImproperlyConfigured:
        if verbosity:
            print 'WARNING: unable to find app = %r' % app
    if verbosity > 2:
        print 'Trying a fuzzy match on app = %r' % app
    app_names = [app_class.__package__ for app_class in djmodels.get_apps() if app_class and app_class.__package__]
    fuzzy_app_name = fuzzy.extractOne(str(app), app_names)[0]
    if verbosity:
        print 'WARNING: Best fuzzy match for app name %r is %s' % (app, fuzzy_app_name)
    return djmodels.get_app(fuzzy_app_name.split('.')[-1])
get_app.default = DEFAULT_APP


def get_model(model=DEFAULT_MODEL, app=None, fuzziness=False):
    """Retrieve a Django model class for the indicated model name and app name (or module object)

    Args:
      model: A model class, queryset or string. E.g. one of:
        * derivative of django.db.models.base.ModelBase
        * derivative of django.db.models.query.QuerySet
        * string name of a django.db.models.Model class that can be found in <app>.models
      app (module): A python module (Django app) or the string name of a Django app.
      fuzziness (float): The allowable levenshtein distance between the model name. (0 < fuzziness < 1)

    Returns:
      Model: a Django model class

    TODO:
      * Parse the model string to see if it contains a model path like 
        'app_name.model_name' or 'app_name.models.model_name'

    Examples:

      >>> from django.db import transaction
      >>> transaction.rollback() 
      >>> get_model('mission', fuzziness=.7).__name__.startswith('Permi')
      True
      >>> transaction.rollback() 
      >>> isinstance(get_model('ser', fuzziness=.5), djmodels.base.ModelBase)
      True
      >>> transaction.rollback() 
      >>> get_model(get_model('CaseMaster', DEFAULT_APP, fuzziness=.05)).objects.count() >= 0
      True

    """
    if isinstance(model, djmodels.base.ModelBase):
        return model
    elif isinstance(model, (djmodels.Manager, djmodels.query.QuerySet)):
        return model.model
    if not app or (isinstance(model, basestring) and '.' in model):
        try:
            app, model = model.split('.')
        except:
            tokens = model.split('.')
            model = tokens[-1]
            app = '.'.join(tokens[:-1])
    # print 'getting model=%r from app=%r' % (model, app)
    try:
        # FIXME: this will turn app into a list of strings if app=None is passed in!!!
        app = get_app(app)
    except:
        pass
        # FIXME: This seems futile! model is still just a string!
        # try:
        #     app = get_app(model.app_label)
        # except:
        #     app = get_app(model._meta.app_label)
    try:
        model_object = djmodels.get_model(app.__package__.split('.')[-1], model)
        if model_object:
            return model_object
    except:
        pass
    try: 
        model_object = djmodels.get_model(app, model)
        if model_object:
            return model_object
    except:
        pass
    if not fuzziness and not model_object:
        return model_object
    app = get_app(app)
    if not app:
        return None
    model_names = [mc.__name__ for mc in djmodels.get_models(app)]
    if app and model and model_names:
        model_name, similarity_score = fuzzy.extractOne(str(model), model_names)
        if similarity_score / 100. + float(fuzziness) >= 1.0:
            return djmodels.get_model(app.__package__.split('.')[-1], model_name)


def get_queryset(qs=None, app=DEFAULT_APP, db_alias=None):
    """
    >>> from django.db import transaction
    >>> transaction.rollback() 
    >>> get_queryset('WikiI').count() > 0
    True
    """
    # print 'get_model' + repr(model) + ' app ' + repr(app)
    if isinstance(qs, (djmodels.Manager, djmodels.query.QuerySet)):
        qs = qs.all()
    else:
        qs = get_model(qs, app=app).objects.all()
    if db_alias:
        return qs.using(db_alias)
    else:
        return qs  # .using(router.db_for_read(model))



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


def get_field(field):
    """Return a field object based on a dot-delimited app.model.field name"""
    if isinstance(field, djmodels.fields.Field):
        return field
    elif isinstance(field, basestring):
        field = field.split('.')
        if len(field) == 3:
            model = get_model(app=field[0], model=field[1])
        elif len(field) == 2:
            model = get_model(app=DEFAULT_APP, model=field[0])
        else:
            return None
            raise NotImplementedError("Unknown default model name. Don't know where to look for field %s" % '.'.join(field)) 
        field = model._meta.get_field(field[-1])
    return field


def get_primary_key(model):
    """Get the name of the field in a model that has primary_key=True"""
    model = get_model(model)
    return (field.name for field in model._meta.fields if field.primary_key).next()


def copy_field(source_field, destination_field_or_model, src_pk_field=None, dest_pk_field=None, overwrite_null=False, skip_null=True, verbosity=1):
    source_field = get_field(source_field)
    destination_field = get_field(destination_field_or_model
                                  or get_model(destination_field_or_model)._meta.get_field())
    max_length = getattr(destination_field, 'max_length', float('inf'))
    src_pk_field = src_pk_field or get_primary_key(source_field.model)
    if not dest_pk_field and src_pk_field in [field.name for field in destination_field.model._meta.fields]:
        dest_pk_field = src_pk_field
    dest_pk_field = dest_pk_field or get_primary_key(destination_field.model)

    dest = destination_field.model.objects.filter(pk__isnull=False)
    if not overwrite_null:
        dest=dest.filter(**{destination_field.name + '__isnull': True})
    src = source_field.model.objects.filter(pk__isnull=False)
    if skip_null:
        src=src.filter(**{source_field.name + '__isnull': False})
    N = src.count()
    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % (N,), pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=N).start()

    for batch_num, batch in enumerate(generate_queryset_batches(src, verbosity=verbosity)):
        updated_objects = []
        for obj in batch:
            if verbosity:
                pbar.update(i)
                i += 1
            try:
                new_obj = dest.get(**{dest_pk_field: getattr(obj, src_pk_field)})
            except dest.model.DoesNotExist:
                if verbosity > 2:
                    print '%r.get(**{%r: %r})' % (dest.model, dest_pk_field, getattr(obj, src_pk_field))
                continue
            new_value = getattr(obj, source_field.name, None)
            if isinstance(new_value, basestring):
                new_value = str.strip(new_value)
                if len(new_value) >  max_length:
                    new_value = new_value[:max_length]
            if new_value:
                setattr(new_obj, destination_field.name, new_value)
                updated_objects += [new_obj]
        if verbosity > 1:
            print 'Fraction of objects that have been updated: %g / %d' % (sum(1 for o in updated_objects if o.rano), len(updated_objects) )
        bulk_update(updated_objects)

    if verbosity:
        pbar.finish()


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
        filter_dicts = util.listify(title_prefix)
    
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
    qs = qs.objects.values(*util.listify(fields))
    qs = [[rec[k] for k in rec] for rec in qs]
    if transpose:
        return util.transposed_lists(qs)
    return qs


def format_fields(x, y, filter_dict={'model__startswith': 'LC60'}, model=DEFAULT_MODEL, app=DEFAULT_APP, count_x=None, 
                  count_y=None, order_by=None, limit=1000, aggregate=None, sum_x=None, sum_y=None):
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
            objects = objects.annotate(y_value=djmodels.Count('pk'))
            y = 'y_value'
        else:
            if count_x:
                objects = objects.annotate(x_value=djmodels.Count(x))
                x = 'x_value'
            if count_y:
                objects = objects.annotate(y_value=djmodels.Count(y))
                y = 'y_value'
            if sum_x:
                objects = objects.annotate(x_value=djmodels.Sum(x))
                x = 'x_value'
            if sum_y:
                objects = objects.annotate(y_value=djmodels.Sum(y))
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
    objects = objects.annotate(y=djmodels.Count(x))
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

    >>> from django.db import transaction
    >>> transaction.rollback()
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
    objects = objects.annotate(count_of_records_per_date_bin=djmodels.Count('pk'))
    
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

    >>> from django.db import transaction
    >>> transaction.rollback()
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
    objects = objects.annotate(y=djmodels.Sum(y))

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
    field_names = util.listify(field_names)
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
    """Use fuzzy string matching to find similar model field names without consulting a synonyms list

    Returns:
      list: A list model field names (strings) sorted from most likely to least likely.
        [] If no similar field names could be found in the indicated model
        [None] If none found and and `pad_with_none` set

    Examples:

      >>> find_fields(['date_time', 'title_prefix', 'sales'], model='WikiItem')
      ['date', 'model', 'net_sales']

    """
    fields = util.listify(fields)
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


def model_from_path(model_path, fuzziness=False):
    """Find the model class for a given model path like 'project.app.model'

    Args:
        path (str): dot-delimited model path, like 'project.app.model'

    Returns:
        Django Model-based class
    """
    app_name = '.'.join(model_path.split('.')[:-1])
    model_name = model_path.split('.')[-1]

    if not app_name:
        return None

    module = importlib.import_module(app_name)
    try:
        model = getattr(module, model_name)
    except AttributeError:
        try:
            model = getattr(getattr(module, 'models'), model_name)
        except AttributeError:
            model = get_model(model_name, app_name, fuzziness=fuzziness)

    return model


def find_synonymous_field(field, model=DEFAULT_MODEL, app=DEFAULT_APP, score_cutoff=50, root_preference=1.02):
    """Use a dictionary of synonyms and fuzzy string matching to find a similarly named field

    Returns:
      A single model field name (string)

    Examples:

      >>> find_synonymous_field('date', model='WikiItem')
      'end_date_time'
      >>> find_synonymous_field('date', model='WikiItem')
      'date_time'
      >>> find_synonymous_field('time', model='WikiItem')
      'date_time'

    """
    fields = util.listify(field) + list(synonyms(field))
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


def find_model(model_name, apps=settings.INSTALLED_APPS, fuzziness=0):
    """Find model_name among indicated Django apps and return Model class

    Examples:
        To find models in an app called "miner":

        >>> find_model('WikiItem', 'miner')
        >>> find_model('Connection', 'miner')
        >>> find_model('InvalidModelName')

    """
    # if it looks like a file system path rather than django project.app.model path the return it as a string
    if '/' in model_name:
        return model_name
    if not apps and isinstance(model_name, basestring) and '.' in model_name:
        apps = [model_name.split('.')[0]]
    apps = util.listify(apps or settings.INSTALLED_APPS)
    for app in apps:
        # print 'getting %r, from app %r' % (model_name, app)
        model = get_model(model=model_name, app=app, fuzziness=fuzziness)
        if model:
            return model
    return None


def find_field(field, model=DEFAULT_MODEL, app=DEFAULT_APP, fuzziness=.5):
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
    return find_fields(field, model, app, score_cutoff=int(fuzziness*100), pad_with_none=True)[0]


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
        x, y = sequence_from_filter_spec([find_synonymous_field(x), find_synonymous_field(y)], filter_dict, model=model, 
                                         app=app, sort=sort, limit=limit)
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
    fields = util.listify(fields)
    N = len(fields)
    models = util.listify(models, N) or [None] * N
    filter_dicts= util.listify(filter_dicts, N) or [{}] * N
    apps = util.listify(apps, N) or [None] * N
    columns = []
    for field, model, app, filter_dict in zip(fields, models, filter_dicts, apps):
        columns += [get_column(field, model, filter_dict, app)]


def ensure_lol(obj, value_type=str, list_type=list):
    """Ensure that an obj is a list of lists of values (2-D table of values).

    Useful for iterating through a django.db.Model.Meta.unique_together list of field names 

    >>> ensure_lol([1,2,3])
    [['1', '2', '3']]
    >>> ensure_lol([1,2,3], value_type=float)
    [[1.0, 2.0, 3.0]]
    >>> ensure_lol([1,2,3], value_type=int)
    [[1, 2, 3]]
    >>> ensure_lol('1,2,3')
    [['1,2,3']]
    >>> ensure_lol(('a', ('b', 'c')))
    [['a', ['b', 'c']]
    """
    print 'FIXME: NOT IMPLEMENTED'
    return obj


def diff_field_names(model0, model1):
    fields0 = set(model0._meta.get_all_field_names())
    fields1 = set(model1._meta.get_all_field_names())
    diff0 = fields0 - fields1
    diff1 = fields1 - fields0
    return fields0 - diff0, diff0, diff1


def shared_field_names(model0, model1):
    diff = diff_field_names(model0, model1)
    return diff[0]


def diff_data(model0, model1, pk_name='pk', field_names=None, ignore_related=True, strip=True, nulls=(0, 0.0, ''), clean_unicode=clean_utf8, short_circuit=False, ignore_field_names=None, verbosity=2, limit=10000):
    nulls = set(nulls) if nulls else set()
    ans = {
        'count': 0,
        'multiple_returned': [],
        'missing': [],
        'mismatches': [],
        'clean_unicode_errors': [],
        'unicode_warnings': [],
        'ascii_mismatches': [],
        'unicode_mismatches': [],
        'field_names_model0': list(set(model0._meta.get_all_field_names())),
        'field_names_model1': list(set(model1._meta.get_all_field_names())),
        'model0': model0._meta.app_label + '.' + model0._meta.module_name,
        'model1': model1._meta.app_label + '.' + model1._meta.module_name,
        }
    if field_names is None:
        field_names = set(ans['field_names_model0']) - (set(ans['field_names_model0']) - set(ans['field_names_model1']))
    linked_field_names = []
    ignore_field_names = set((ignore_field_names or []) + 
        list(getattr(model0, '_UNLISTABLE_FIELDS', [])) + 
        list(getattr(model1, '_UNLISTABLE_FIELDS', [])))
    for name in field_names:
        if name in ignore_field_names:
            continue
        field = model0._meta.get_field(name)
        if isinstance(field, related.RelatedField):
            if not ignore_related:
                linked_field_names += [name + '_id']
        else:
            linked_field_names += [name]
    ans['field_names'] = list(linked_field_names)
    ans['fields_ignored'] = list(ignore_field_names)
    qs = model0.objects.filter(**{pk_name + '__isnull': False})
    N = qs.count()
    if limit and 0 < limit < N:
        qs = qs.order_by('?')
    else:
        limit = N
    if verbosity:
        widgets = [pb.Counter(), '/%d records: ' % limit, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=limit).start()

    batch_num = 0
    for batch0 in util.generate_slices(qs, batch_len=999):
        #batch1 = model1.objects.filter(**{pk_name + '__in': batch0.values_list(pk_name, flat=True)}).all()
        batch_num += 1
        if i > limit:
            break
        for obj0 in batch0:
            if verbosity:
                pbar.update(i)
            i += 1
            if i > limit:
                # if model0 records are added during this loop, then some records will not be checked
                break
            pk = getattr(obj0, pk_name)
            try:
                obj1 = model1.objects.get(**{pk_name: pk}) # batch1.get(**{pk_name: pk})
            except model0.MultipleObjectsReturned:
                ans['multiple_returned'] += [pk]
            except model0.DoesNotExist:
                ans['missing'] += [pk]
            except:
                print_exc()
                import ipdb
                ipdb.set_trace()
            mismatched_fields = []
            for fn in linked_field_names:
                val0, val1 = getattr(obj0, fn), getattr(obj1, fn)
                try:
                    if val0 == val1:
                        continue
                except UnicodeWarning:
                    if verbosity > 1:
                        print_exc()
                        ans['unicode_warnings'] += [(pk, fn)]
                if nulls:
                    if (val0 is None and val1 in nulls) or (val1 is None and val0 in nulls):
                        continue
                if isinstance(val0, basestring) and isinstance(val1, basestring): 
                    if strip:
                        try:
                            val0, val1 = val0.strip(), val1.strip()
                            if val0 == val1:
                                continue
                        except:
                            pass
                    if clean_unicode:
                        try:
                            val0, val1 = clean_unicode(val0), clean_unicode(val1)
                        except:
                            if verbosity > 1:
                                print_exc()
                            ans['clean_unicode_errors'] += [(pk, fn)]
                        try:
                            if val0 == val1:
                                continue
                            else:
                                ans['unicode_mismatches'] += [(pk, fn)]
                        except UnicodeWarning:
                            pass
                        val0, val1 = replace_nonascii(val0, ''), replace_nonascii(val1, '')
                        if val0 == val1:
                            continue
                        else:
                            ans['ascii_mismatches'] += [(pk, fn)]
                            if verbosity > 2:
                                print 'ASCII MISMATCH: %r != %r' % (val0, val1)
                if verbosity > 2:
                    print 'MISMATCH: %r != %r' % (val0, val1)
                mismatched_fields += [fn]
                if short_circuit:
                    break
            if not mismatched_fields:
                ans['count'] += 1
            else:
                ans['mismatches'] += [(pk, mismatched_fields)]
                if verbosity > 1:
                    print '='*20 + ' ' + str(pk) + ' ' + '='*20
                    print dict([(k, (val0, val1)) for k in mismatched_fields])
                    print '-'*50
    if verbosity:
        pbar.finish()
    return ans


class Columns(collections.OrderedDict):
    """A collections.OrderedDict of named columns of data, similar to a pandas DataFrame

         `collections.OrderedDict([('name1', [x11, x21, ..., xM1]), ... ('nameM', [x1, ... objNM])]`

          similar to a Pandas `DataFrame`, but with the added convenience functions for DB I/O
          and numpy data processing (though pandas is now more numpy-friendly)

    keys of collections.OrderedDict are the column (db field) names
        prefixed with the app and and table name if ambiguous
    The attribute `Columns.db_fields` is an collections.OrderedDict which stores a list of tuples 
        `(app_name, table_name, column_name, db_filter_dict)` 
        using the same keys as the Columns collections.OrderedDict data container

    values of the collections.OrderedDict
    """
    default_app = DEFAULT_APP
    default_table = DEFAULT_MODEL
    # FIXME: default args need to be replaced by None and this value substituted, if necessary
    default_ddof = 0
    default_tall = True
    db_fields = None
    len_column = None

    def __init__(self, *args, **kwargs):
        fields = util.listify(kwargs.get('fields', None), N=self.len_column)
        filters = util.listify(kwargs.get('filters', None), N=self.len_column)
        tables = util.listify(kwargs.get('tables', None), N=self.len_column)
        apps = util.listify(kwargs.get('apps', None), N=self.len_column)

        super(Columns, self).__init__()
        # TODO: DRY up the redundancy
        for arg_name in ('fields', 'filters', 'tables', 'apps'):
            locals()[arg_name] = util.listify(locals()[arg_name], N=self.len_column)
            self.len_column = max(self.len_column, len(locals()[arg_name]))

        kwargs = self.process_kwargs(kwargs, prefix='default_', delete=True)

        split_fields = [re.split(r'\W|__', field, maxsplit=3) for field in fields]
        if filters and not fields:
            split_fields = [re.split(r'\W|__', iter(d).next(), maxsplit=3) for d in filters]

        for i, arg_name in enumerate(('apps', 'tables', 'fields')):
            if not locals()[arg_name]:
                locals()[arg_name] = util.listify((sf[min(i, len(sf) - 1)] for sf in split_fields), N=self.len_column)
        
        if not apps or not apps[0] or apps[0].strip() == '.':
            apps = util.listify(self.default_app, self.len_column)
        self.default_app = apps[0]

        self.db_fields = collections.OrderedDict((fields[i], (apps[i], tables[i], fields[i], filters[i])) for i in range(self.len_column))

        if len(args) == 1:
            if isinstance(args[0], basestring):
                self.from_string(args[0])
            elif isinstance(args[0], djmodels.query.ValuesQuerySet) or hasattr(args[0], '__iter__'):
                if isinstance(iter(args[0]).next(), collections.Mapping):
                    self.from_valuesqueryset(args[0])
                else:
                    self.from_row_wise_lists(args[0], **kwargs)
            elif isinstance(args[0], djmodels.query.QuerySet):
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
                if not isinstance(d, collections.Mapping):
                    if not all(isinstance(name, basestring) for name in self):
                        for name in self:
                            del(self[name])
                        for j, val in enumerate(d):
                            self[j] = val
                    names = list(self)
                    # the first row has already been processed (as either column names or column values), so move right along
                    continue
            if not isinstance(d, collections.Mapping):
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


def django_object_from_row(row, model, field_names=None, ignore_fields=('id', 'pk'), ignore_related=True, strip=True, ignore_errors=True, verbosity=0):
    """Construct Django model instance from values provided in a python dict or Mapping

    Args:
      row (list or dict): Data (values of any type) to be assigned to fields in the Django object.
        If `row` is a list, then the column names (header row) can be provided in `field_names`.
        If `row` is a list and no field_names are provided, then `field_names` will be taken from the 
        Django model class field names, in the order they appear within the class definition.
      model (django.db.models.Model): The model class to be constructed with data from `row`
      field_names (list or tuple of str): The field names to place the row values in. 
        Defaults to the keys of the dict of `row` (if `row` is a `dict`) or the names of the fields
        in the Django model being constructed.
      ignore_fields (list or tuple of str): The field names to ignore if place the row values in. 

    Returns:
      Model instance: Django model instance constructed with values from `row` in fields
        from `field_names` or `model`'s fields
    """
    field_dict, errors = field_dict_from_row(row, model, field_names=field_names, ignore_fields=ignore_fields, strip=strip,
                                             ignore_errors=ignore_errors, ignore_related=ignore_related, verbosity=verbosity)
    if verbosity >= 3:
        print 'field_dict = %r' % field_dict
    try:
        obj = model(**field_dict)
        return obj, errors
    except:
        print_exc()
        raise ValueError('Unable to coerce the dict = %r into a %r object' % (field_dict, model))


def field_dict_from_row(row, model,
                        field_names=None, ignore_fields=('id', 'pk'), 
                        strip=True, 
                        blank_none=True, 
                        ignore_related=True, 
                        ignore_values=(None,), 
                        ignore_errors=True, 
                        verbosity=0):
    """Construct a Mapping (dict) from field names to values from a row of data

    Args:
      row (list or dict): Data (values) to be assigned to field_names in the dict.
        If `row` is a list, then the column names (header row) can be provided in `field_names`.
        If `row` is a list and no field_names are provided, then `field_names` will be taken from the 
        Django model class field names, in the order they appear within the class definition.
      model (django.db.models.Model): The model class to be constructed with data from `row`
      field_names (list or tuple of str): The field names to place the row values in. 
        Defaults to the keys of the dict of `row` (if `row` is a `dict`) or the names of the fields
        in the Django model being constructed.
      ignore_fields (list or tuple of str): The field names to ignore if place the row values in. 

    Returns:
      dict: Mapping from fields to values compatible with a Django model constructor kwargs, `model(**kwargs)`
    """
    errors = collections.Counter()
    if not field_names:
        field_classes = [f for f in model._meta._fields() if (not ignore_fields or (f.name not in ignore_fields))]
        field_names = [f.name for f in field_classes]
    else:
        field_classes = [f for f in model._meta._fields() if (f.name in field_names and (not ignore_fields or (f.name not in ignore_fields)))]
    field_dict = {}
    if isinstance(row, collections.Mapping):
        row = [row.get(field_name, None) for field_name in field_names]
    # if most of the destination field names exist in the source object then 
    elif sum(hasattr(row, field_name) for field_name in field_names) / (len(field_names) / 2. + 1):
        row = [getattr(row, field_name, None) for field_name in field_names]
    for field_name, field_class, value in zip(field_names, field_classes, row):
        clean_value = None
        if verbosity >= 3:
            print field_name, field_class, value
        if isinstance(field_class, related.RelatedField):
            if not ignore_related:
                try:
                    clean_value = field_class.related.parent_model.objects.get(value)
                except:
                    try:
                        clean_value = field_class.related.parent_model.objects.get_by_natural_key(value)
                    except:
                        errors += collections.Counter(['num_unlinked_fks'])
                        if verbosity > 1:
                            print 'Unable to connect related field %r using value %r' % (field_class, value)
        # FIXME: lots of redundancy and potential for error here and below
        if isinstance(value, basestring) and not value:
            if verbosity >= 3:
                print 'String field %r setting value %r to None' % (field_class, value)
            value = None
            if blank_none and (
                not isinstance(field_class, related.RelatedField) or field_class.blank or not field_class.null):
                try:
                    if isinstance(field_class.to_python(''), basestring):
                        value = ''
                    else:
                        value = None
                except:
                    value = None
            else:
                value = None
        if not clean_value:
            try:
                # get a clean python value from a string, etc
                clean_value = field_class.to_python(value)
            except:  # ValidationError
                try:
                    clean_value = str(field_class.to_python(util.clean_wiki_datetime(value)))
                except:
                    try:
                        clean_value = field_class.to_python(util.make_float(value))
                    except:
                        try:
                            clean_value = field_class.to_python(value)  # FIXME: this has already been tried!
                        except:
                            if verbosity:
                                print
                                print "The row below has a value (%r) that can't be coerced by %r:" % (value, field_class.to_python)
                                print row
                                print_exc()
                            clean_value = None
                            errors += collections.Counter(['num_uncoercible'])
                            if not ignore_errors:
                                raise
        if isinstance(clean_value, basestring):
            if strip:
                clean_value = clean_value.strip()
            # don't forget to decode the utf8 before doing a max_length truncation!
            clean_value = clean_utf8(clean_value, verbosity=verbosity).decode('utf8')
            max_length = getattr(field_class, 'max_length')
            if max_length:
                try:
                    assert(len(clean_value) <= field_class.max_length)
                except:
                    if verbosity:
                        print
                        print "The row below has a string (%r) that is too long (> %d):" % (clean_value, max_length)
                        print row
                        print_exc()
                        errors += collections.Counter(['num_truncated'])
                    clean_value = clean_value[:max_length]
                    if not ignore_errors:
                        raise  
        if not ignore_values or clean_value not in ignore_values:
            field_dict[field_name] = clean_value
    return field_dict, errors


def count_lines(fname, mode='rU'):
    '''Count the number of lines in a file

    Only faster way would be to utilize multiple processor cores to perform parallel reads.
    http://stackoverflow.com/q/845058/623735
    '''

    with open(fname, mode) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def clear_model(model, dry_run=True, verbosity=1):
    '''Delete all data records in a model, obeying `clear`, `dry_run`, and `verbosity` flags
    
    If a clear was requested (dry_run or otherwise), return the number of records deleted (# before minus # after)
    '''
    N_existing = model.objects.count()
    if dry_run:
        print "DRY_RUN: NOT deleting %d records in %r." % (model.objects.all().count(), model)
    if N_existing:
        ans = 'y'
        if verbosity and not dry_run:
            ans = raw_input('Are you sure you want to delete all %d existing database records in %r? (y/n) ' % (N_existing, model))
        if ans.lower().startswith('y') and not dry_run:
            model.objects.all().delete()
        return N_existing - model.objects.count()
    return 0


def load_csv_to_model(path, model, field_names=None, delimiter=None, batch_len=10000, 
                      dialect=None, num_header_rows=1, mode='rUb',
                      strip=True, clear=False, dry_run=True, ignore_errors=True, verbosity=2):
    '''Bulk create database records from batches of rows in a csv file.'''

    reader_kwargs = {}
    errors = collections.Counter()
    if delimiter or dialect:
        reader_kwargs['dialect'] = dialect or 'excel'
        if delimiter:
            reader_kwargs['delimiter'] = delimiter
    reader_kwargs['delimiter'] = str(reader_kwargs['delimiter'][0])
    delimiter = reader_kwargs['delimiter']

    path = path or './'
    if not delimiter:
        for d in ',', '|', '\t', ';':
            try:
                return load_csv_to_model(path=path, model=model, field_names=field_names, delimiter=d, batch_len=batch_len,
                                         dialect=dialect, num_header_rows=num_header_rows,
                                         strip=strip, clear=clear, dry_run=dry_run, ignore_errors=ignore_errors, verbosity=verbosity)
            except:
                pass
        return None

    if clear:
        clear_model(model, dry_run=dry_run, verbosity=verbosity)

    M = 0
    with open(path, mode) as f:
        reader = csv.reader(f, **reader_kwargs)
        header_rows = []
        i = 0
        while len(header_rows) < num_header_rows and i < 100:
            row = reader.next()
            i += 1
            if not row or any(compiled_regex.match(row[0]) for compiled_regex in header_rows_to_ignore):
                if verbosity > 1:
                    print 'IGNORED: %r' % row
            else:
                header_rows += [row]
        if verbosity > 2:
            print 'HEADER: %r' % header_rows
        if verbosity:
            N = count_lines(path, mode) - i + 10  # + 10 fudge factor in case multiple newlines in a single csv row
            widgets = [pb.Counter(), '/%d lines: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
            i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=N).start()
        if verbosity > 3:
            print 'Generating all the batches before iterating may take a while...'
        for batch_num, batch_of_rows in enumerate(util.generate_batches(reader, batch_len)):
            if verbosity > 2:
                print 
                print i
            batch_of_objects = []
            for j, row in enumerate(batch_of_rows):
                if verbosity > 3:
                    print j, row
                if not row or all(not el for el in row):
                    if verbosity > 2:
                        print 'IGNORED: %r' % row
                    continue
                if verbosity or not ignore_errors:
                    M = M or len(row)
                    if len(row) != M:
                        print 'ERROR importing row #%d in batch_num=%d which is row #%d overall. The row had %d columns, but previous rows had %d.' % (j + 1, batch_num + 1, i + j + 1, len(row), M)
                        print 'Erroneously parsed row:'
                        print repr(row)
                        
                        if not ignore_errors:
                            raise ValueError('ERROR importing row #%d which had %d columns, but previous rows had %d.' % (i + j + 1, len(row), M))
                try:
                    obj, row_errors = django_object_from_row(row, model=model, field_names=field_names, strip=strip, verbosity=verbosity)
                    batch_of_objects += [obj]
                    errors += row_errors
                except:
                    if verbosity:
                        print 'Error importing row #%d' % (i + j + 1)
                        print_exc()
                    if not ignore_errors:
                        raise
                if verbosity:
                    try:
                        pbar.update(i + j)
                    except:
                        print_exc()
                        if not ignore_errors:
                            raise
            i += len(batch_of_rows)
            if not dry_run:
                model.objects.bulk_create(batch_of_objects)
            elif verbosity:
                print "DRY_RUN: NOT bulk creating batch of %d records in %r" % (len(batch_of_objects), model)
        if verbosity:
            pbar.finish()
    return i
header_rows_to_ignore = [re.compile(r'^\s*[Dd]irectory\:.*$'), re.compile(r'^\s*[Nn]ame\:.*$'), re.compile(r'^\s*[-=_]+\s*$')]


def path_size(path, total=False, ext='', level=None, verbosity=0):
    """Walk the file tree and query the file.stat object(s) to compute their total (or individual) size in bytes

    Returns:
      dict: {relative_path: file_size_in_bytes, ...}

    Examples:
      >>> all(d >= 0 for d in path_size(__file__).values())
      True
      >>> sum(path_size(os.path.dirname(__file__)).values()) == path_size(os.path.dirname(__file__), total=True)
      True
      >>> path_size(__file__, total=True) > 10000
      True
      >>> len(path_size('.')) >= 2
      True
    """
    dict_of_path_sizes = dict((d['path'], d['size']) for d in find_files(path, ext=ext, level=level, verbosity=0))
    if total:
        return reduce(lambda tot, size: tot + size, dict_of_path_sizes.values(), 0)
    return dict_of_path_sizes


def load_all_csvs_to_model(path, model, field_names=None, delimiter=None, batch_len=10000,
                           dialect=None, num_header_rows=1, mode='rUb',
                           strip=True, clear=False, dry_run=True, ignore_errors=True,
                           sort_files=True, recursive=False, ext='',
                           min_mod_date=None, max_mod_date=None,
                           verbosity=2):
    """Bulk create database records from all csv files found within a directory."""
    if min_mod_date and isinstance(min_mod_date, basestring):
        min_mod_date = parse_date(min_mod_date)
    if isinstance(min_mod_date, datetime.date):
        min_mod_date = datetime.datetime.combine(min_mod_date, datetime.datetime.min.time())

    if max_mod_date and isinstance(max_mod_date, basestring):
        max_mod_date = parse_date(max_mod_date)
    if isinstance(max_mod_date, datetime.date):
        max_mod_date = datetime.datetime.combine(max_mod_date, datetime.datetime.min.time())

    path = path or './'
    batch_len = batch_len or 1000
    if verbosity:
        if dry_run:
            print 'DRY_RUN: actions will not modify the database.'
        else:
            print 'THIS IS NOT A DRY RUN, THESE ACTIONS WILL MODIFY THE DATABASE!!!!!!!!!'

    if clear:
        clear_model(model, dry_run=dry_run, verbosity=verbosity)

    file_dicts = find_files(path, ext=ext, level=None if recursive else 0, verbosity=verbosity)
    file_bytes = reduce(lambda a,b: a+b['size'], file_dicts, 0)

    if sort_files:
        file_dicts = sorted(file_dicts, key=itemgetter('path'))
    if verbosity > 1:
        print file_dicts
    if verbosity:
        widgets = [pb.Counter(), '/%d bytes for all files: ' % file_bytes, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=file_bytes)
        pbar.start()
    N = 0
    file_bytes_done = 0
    for meta in file_dicts:
        if (min_mod_date and meta['modified'] < min_mod_date) or (max_mod_date and meta['modified'] > max_mod_date):
            if verbosity > 1:
                print("Skipping {0} because it's mdate is not between {1} and {2}".format(meta['path'], min_mod_date, max_mod_date))
            continue
        if verbosity:
            print
            print 'Loading "%s"...' % meta['path']
        N += load_csv_to_model(path=meta['path'], model=model, field_names=field_names, delimiter=delimiter, batch_len=batch_len, 
                               dialect=dialect, num_header_rows=num_header_rows, mode=mode,
                               strip=strip, clear=False, dry_run=dry_run, 
                               ignore_errors=ignore_errors, verbosity=verbosity)
        if verbosity:
            file_bytes_done += meta['size']
            pbar.update(file_bytes_done)
    if verbosity:
        pbar.finish()
    return N


def walk_level(path, level=1):
    """Like os.walk, but takes `level` kwarg that indicates how deep the recursion will go.

    Notes:
      TODO: refactor `level`->`depth`

    References:
      http://stackoverflow.com/a/234329/623735

    Args:
      path (str):  Root path to begin file tree traversal (walk)
      level (int, optional): Depth of file tree to halt recursion at. 
        None = full recursion to as deep as it goes
        0 = nonrecursive, just provide a list of files at the root level of the tree
        1 = one level of depth deeper in the tree

    Examples:
      >>> root = os.path.dirname(__file__)
      >>> all((os.path.join(base,d).count('/')==(root.count('/')+1)) for (base, dirs, files) in walk_level(root, level=0) for d in dirs)
      True
    """
    if isinstance(level, NoneType):
        level = float('inf')
    path = path.rstrip(os.path.sep)
    if os.path.isdir(path):
        root_level = path.count(os.path.sep)
        for root, dirs, files in os.walk(path):
            yield root, dirs, files
            if root.count(os.path.sep) >= root_level + level:
                del dirs[:]
    else:
        assert os.path.isfile(path)
        yield os.path.dirname(path), [], [os.path.basename(path)]


def find_files(path, ext='', level=None, verbosity=0):
    """Recursively find all files in the indicated directory with the indicated file name extension

    Args:
      path (str):
      ext (str):   File name extension. Only file paths that ".endswith()" this string will be returned
      level (int, optional): Depth of file tree to halt recursion at. 
        None = full recursion to as deep as it goes
        0 = nonrecursive, just provide a list of files at the root level of the tree
        1 = one level of depth deeper in the tree

    Returns: 
      list of dicts: dict keys are { 'path', 'name', 'bytes', 'created', 'modified', 'accessed', 'permissions' }
        path (str): Full, absolute paths to file beneath the indicated directory and ending with `ext`
        name (str): File name only (everythin after the last slash in the path)
        size (int): File size in bytes
        created (datetime): File creation timestamp from file system
        modified (datetime): File modification timestamp from file system
        accessed (datetime): File access timestamp from file system
        permissions (int): File permissions bytes as a chown-style integer with a maximum of 4 digits 
          e.g.: 777 or 1755

    Examples:
      >>> sorted(d['name'] for d in find_files(os.path.dirname(__file__), ext='.py', level=0))[0]
      '__init__.py'
    """
    path = path or './'
    files_in_queue = []
    if verbosity:
        print 'Preprocessing files to estimate pb.ETA'
    # if verbosity:
    #     widgets = [pb.Counter(), '/%d bytes for all files: ' % file_bytes, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
    #     i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=file_bytes)
    #     print pbar
    #     pbar.start()
    for dir_path, dir_names, filenames in walk_level(path, level=level):
        for fn in filenames:
            if ext and not fn.lower().endswith(ext):
                continue
            files_in_queue += [{'name': fn, 'path': os.path.join(dir_path, fn)}]
            files_in_queue[-1]['size'] = os.path.getsize(files_in_queue[-1]['path'])
            files_in_queue[-1]['accessed'] = datetime.datetime.fromtimestamp(os.path.getatime(files_in_queue[-1]['path']))
            files_in_queue[-1]['modified'] = datetime.datetime.fromtimestamp(os.path.getmtime(files_in_queue[-1]['path']))
            files_in_queue[-1]['created'] = datetime.datetime.fromtimestamp(os.path.getctime(files_in_queue[-1]['path']))
            # file_bytes += files_in_queue[-1]['size']
    if verbosity > 1:
        print files_in_queue
    return files_in_queue


def clean_duplicates(model, unique_together=('serial_number',), date_field='created_on',
                     seq_field='seq', seq_max_field='seq_max', ignore_existing=True, verbosity=1):
    qs = getattr(model, 'objects', model)
    if ignore_existing:
        qs = qs.filter(**{seq_max_field + '__isnull': True})
    qs = qs.order_by(*(util.listify(unique_together) + util.listify(date_field)))
    N = qs.count()

    if verbosity:
        print 'Retrieving the first of %d records for %r.' % (N, model)
    qs = qs.all()

    i, dupes = 0, []
    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        pbar = pb.ProgressBar(widgets=widgets, maxval=N+1000).start()       
    for obj in qs:
        if verbosity:
            pbar.update(i)
        if i and all([getattr(obj, f, None) == getattr(dupes[0], f, None) for f in unique_together]):
            dupes += [obj]
        else:
            if len(dupes) > 1:
                for j in range(len(dupes)):
                    setattr(dupes[j], seq_field, j)
                    setattr(dupes[j], seq_max_field, len(dupes) - 1)
                    dupes[j].save()
            else:
                # TODO: speed up by doing a bulk_update
                setattr(obj, seq_field, 0)
                setattr(obj, seq_max_field, 0)
                obj.save()
            dupes = [obj]
        i += 1
    if verbosity:
        pbar.finish()


def hash_model_values(model, clear=True, hash_field='values_hash', hash_fun=hash, ignore_pk=True, ignore_fields=[]):
    """Hash values of DB table records to facilitate tracking changes to the DB table

    Intended for comparing records in one table to those in another (with potentially differing id/pk values)
    For example, changes to a table in a read-only MS SQL database can be quickly identified
    and mirrored to a writeable PostGRE DB where these hash values are stored along side the data.
    """
    qs = getattr(model, 'objects', model)
    model = qs.model
    if ignore_pk:
        ignore_fields += [model._meta.pk.name]
    if not hasattr(model, hash_field):
        warnings.warn("%r doesn't have a field named %s in which to store a hash value. Skipping." % (model, hash_field))
        return
    for obj in qs:
        # ignore primary key (id field) when hashing values
        h = hash_fun(tuple([getattr(obj, k) for k in obj._meta.get_all_field_names() if k not in ignore_fields]))
        tracking_obj, created = ChangeLog.get_or_create(app=model._meta.app_label, model=model._meta.object_name, primary_key=obj.pk)
        tracking_obj.update(hash_value=h)


def delete_in_batches(queryset, batch_len=10000, verbosity=1):
    N = queryset.count()
    if not N:
        return N

    if verbosity:
        print('Deleting %r records from %r...' % (N, queryset.model))
        widgets = [pb.Counter(), '/%d rows: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=N).start()

    for j in range(int(N/float(batch_len)) + 1):
        if i + batch_len < N:
            pk = queryset.order_by('pk').values_list('pk', flat=True).all()[batch_len]
        else:
            pk = None
        pbar.update(i)
        if pk:
            queryset.filter(pk__lt=pk).delete()
            i += batch_len
        else:
            i += queryset.count()
            queryset.all().delete()
            break
    pbar.finish()
    return i


##############################################################
# These import_* functions attempt to import data from one model into another
# They load the entire table into RAM despite creating generators of batches to load

def import_items(item_seq, dest_model,  batch_len=500, 
                 clear=False, dry_run=True, 
                 start_batch=0, end_batch=None, 
                 overwrite=True,
                 run_update=False, ignore_related=True,
                 ignore_errors=False, verbosity=1):
    """Import a sequence (queryset.values(), generator, tuple, list) of dicts into the given model

    """
    if isinstance(dest_model, (djmodels.query.QuerySet, djmodels.Manager)):
        dest_qs = dest_model.all()
        dest_model = get_model(dest_qs)
    else:
        dest_qs = dest_model.objects.all()

    stats = collections.Counter()
    try:
        try:
            src_qs = item_seq.objects.all()
        except AttributeError:
            src_qs = item_seq.all()
        N = src_qs.count()
        item_seq = src_qs.values()
    except AttributeError as e:
        print_exc()
        if not ignore_errors:
            raise e
        N = len(item_seq)

    if not N:
        if verbosity:
            print 'No records found in %r' % src_qs
        return N

    if clear and not dry_run:
        if N < dest_qs.count():
            if verbosity:
                print "WARNING: There are %d %r records in the destinsation queryset which is more than the %d records in the source data. So no records will be deleted/cleared in the destination!" % (dest_qs.count(), dest_model, N)

        if verbosity:
            print "WARNING: Deleting %d records from %r to make room for %d new records !!!!!!!" % (dest_qs.count(), dest_model, N)
        num_deleted = delete_in_batches(dest_qs)
        if verbosity:
            print "Finished deleting %d records in %r." % (num_deleted, dest_model)

    if verbosity:
        print('Loading %r records from sequence provided...' % N)
        widgets = [pb.Counter(), '/%d rows: ' % N or 1, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        pbar = pb.ProgressBar(widgets=widgets, maxval=N)

    for batch_num, dict_batch in enumerate(util.generate_slices(item_seq, batch_len)):
        if batch_num < start_batch:
            if verbosity > 1:
                print('Skipping batch {0} because not between {1} and {2}'.format(batch_num, start_batch, end_batch))
            continue
        elif end_batch and (batch_num > end_batch):
            if verbosity > 1:
                print('Stopping before batch {0} because it is not between {1} and {2}'.format(batch_num, start_batch, end_batch))
            break
        if verbosity > 2:
            print '-------- dict batch ------'
            # print(repr(dict_batch))
            print(repr((batch_num, len(dict_batch), batch_len)))
        item_batch = []

        # convert an iterable of Django ORM record dictionaries into a list of Django ORM objects
        for d in dict_batch:
            if verbosity > 2:
                print '-------- dict of source obj ------'
                print(repr(d))
            obj = dest_model()
            try:
                # if the model has an import_item method then use it
                obj.import_item(d, verbosity=verbosity)
            except:
                if verbosity > 2:
                    print '------ Creating a new %r instance --------' % dest_model
                obj, row_errors = django_object_from_row(d, dest_model, ignore_related=ignore_related, verbosity=verbosity)
                if verbosity > 2:
                    print 'new obj.__dict__: %r' % obj.__dict__
            if run_update:
                try:
                    if verbosity > 2:
                        print '------ Updating FKs with overwrite=%r --------' % overwrite
                    obj._update(save=False, overwrite=overwrite)
                except:
                    if verbosity:
                        print_exc()
                        print 'ERROR: Unable to update record: %r' % obj
                    pass
            item_batch += [obj]
            stats += row_errors

        del(dict_batch)
        # make sure there's a valid last batch number so the verbose messages will make sense
        end_batch = end_batch or int(N / float(batch_len))
        if verbosity and verbosity < 2:
            if batch_num:
                pbar.update(batch_num * batch_len + len(item_batch))
            else:
                # don't start the progress bar until at least one batch has been loaded
                pbar.start()
        elif verbosity > 1:
            print('Writing {0} items (of type {1}) from batch {2}. Will stop at batch {3} which is record {4} ...'.format(
                len(item_batch), dest_model, batch_num, end_batch , min(end_batch * batch_len, N),
                ))

        # use bulk_create to make fast DB insertions. Note: any custom save() or _update() methods will *NOT* be run
        if not dry_run:
            try:
                dest_model.objects.bulk_create(item_batch)
            except UnicodeDecodeError as err:
                from django.db import transaction
                connection._rollback()
                if verbosity:
                    print '%s' % err
                    print 'Now attempting to save objects one at a time instead of as a batch...'
                for obj in item_batch:
                    try:
                        obj.save()
                        stats += collections.Counter(['batch_UnicodeDecodeError'])
                    except:
                        from django.db import transaction
                        connection._rollback()
                        stats += collections.Counter(['save_UnicodeDecodeError'])
                        print str(obj)
                        print repr(obj.__dict__)
                if not ignore_errors:
                    print_exc()
                    raise
            except Exception as err:
                from django.db import transaction
                connection._rollback()
                if verbosity:
                    print '%s' % err
                    print 'Now attempting to save objects one at a time instead of as a batch...'
                for obj in item_batch:
                    try:
                        obj.save()
                        stats += collections.Counter(['batch_Error'])
                    except:
                        from django.db import transaction
                        connection._rollback()
                        print str(obj)
                        print repr(obj.__dict__)
                        print_exc()
                        stats += collections.Counter(['save_Error'])
                if not ignore_errors:
                    print_exc()
                    raise
        del(item_batch)

    if verbosity:
        pbar.finish()
    return stats


def update_items(item_seq,  batch_len=500, dry_run=True, start_batch=0, end_batch=None, ignore_errors=False, verbosity=1):
    """Given a sequence (queryset, generator, tuple, list) of dicts run the _update method on them and do bulk_update"""
    stats = collections.Counter()
    try:
        try:
            src_qs = item_seq.objects.all()
        except AttributeError:
            src_qs = item_seq.all()
        N = src_qs.count()
        item_seq = iter(src_qs)
    except AttributeError:
        print_exc()
        N = item_seq.count()

    if not N:
        if verbosity:
            print 'No records found in %r' % src_qs
        return N

    if verbosity:
        print('Updating %r records in the provided queryset, sequence or model...' % N)
        widgets = [pb.Counter(), '/%d rows: ' % N or 1, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        pbar = pb.ProgressBar(widgets=widgets, maxval=N).start()

    for batch_num, obj_batch in enumerate(util.generate_batches(item_seq, batch_len)):
        if batch_num < start_batch:
            if verbosity > 1:
                print('Skipping batch {0} because not between {1} and {2}'.format(batch_num, start_batch, end_batch))
            continue
        elif end_batch and (batch_num > end_batch):
            if verbosity > 1:
                print('Stopping before batch {0} because it is not between {1} and {2}'.format(batch_num, start_batch, end_batch))
            break
        for obj in obj_batch:
            if verbosity > 2:
                print(repr(obj))
            try:
                if hasattr(obj, '_update'):
                    obj._update(save=False, overwrite=False)
            except:
                if verbosity:
                    print_exc()
                    print 'ERROR: Unable to update record: %r' % obj
                pass
        if verbosity and verbosity < 2:
            pbar.update(batch_num * batch_len + len(obj_batch))
        elif verbosity > 1:
            print('Writing {0} items (of type {1}) from batch {2}. Will stop at batch {3} which is record {4} ...'.format(
                len(obj_batch), src_qs.model, batch_num, end_batch or int((end_batch or N) / float(batch_len)), N
                ))
        if not dry_run:
            try:
                bulk_update(obj_batch, ignore_errors=ignore_errors, delete_first=True, verbosity=verbosity)
            except Exception as err:
                from django.db import transaction
                connection._rollback()
                if verbosity:
                    print '%s' % err
                    print 'Now attempting tp save objects one at a time instead of as a batch...'
                for obj in obj_batch:
                    try:
                        obj.save()
                        stats += collections.Counter(['batch_Error'])
                    except:
                        from django.db import transaction
                        connection._rollback()
                        print str(obj)
                        print repr(obj.__dict__)
                        print_exc()
                        stats += collections.Counter(['save_Error'])
                if not ignore_errors:
                    print_exc()
                    raise

    if verbosity:
        pbar.finish()
    return stats


def import_queryset_batches(qs, dest_qs,  batch_len=500, clear=None, dry_run=True, verbosity=1):
    """Given a sequence (queryset, generator, tuple, list) of dicts import them into the given model

    FIXME: How is this differenct from import_items above?

    clear = model or queryset to be deleted/cleared 
        False: do not clear/delete anything
        None: clear/delete the dest_qs
        True: clear all records in dest_qs.model (e.g. dest_qs.model.objects.all().delete())

    Typical Usage:
    
    >> from src_app.models import SrcModel
    >> from dest_app.models import DestModel
    >> filter_dict={"model__startswith": "LC", "recvdat__gt":'2013-03-31'}
    >> dest = DestModel.objects.filter(**filter_dict)
    >> src = SrcModel.objects.filter(**filter_dict)
    >> src.count(), dest.count()
    >> from pug.nlp import djdb
    >> djdb.import_queryset_batches(src, dest, batch_len=1000, clear=dest, dry_run=False, verbosity=2)
    """
    qs = get_queryset(qs)
    dest_qs = get_queryset(dest_qs)
    dest_model = get_model(dest_qs)

    N = qs.count()

    if verbosity:
        print('Loading %r records from the queryset provided...' % N)
    qs = qs.values()

    if clear is None:
        clear = dest_qs
    if clear and not dry_run:
        if clear == True:
            clear = dest_model.objects.all()
        if verbosity:
            print "WARNING: Deleting %d records from %r !!!!!!!" % (clear.count(), clear.model)
        clear.delete()
    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        pbar = pb.ProgressBar(widgets=widgets, maxval=N).start()
    for batch_num, dict_batch in enumerate(generate_queryset_batches(qs, batch_len)):
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
            pbar.update(batch_num * batch_len + len(dict_batch))
        elif verbosity > 1:
            print(('DRYRUN:  ' if dry_run else '') + 'Writing {0} items in batch {1} out of {2} batches to the {3} model...'.format(
                len(item_batch), batch_num, int(N / float(batch_len)), dest_model))
        if not dry_run:
            dest_model.objects.bulk_create(item_batch)
    if verbosity:
        pbar.finish()

#from django.db.models.fields.related import ForeignKey

def import_queryset(qs, dest_model,  clear=False, dry_run=True, verbosity=1):
    """Given a sequence (queryset, generator, tuple, list) of dicts import them into the given model"""

    # # FIXME: use this info to connect relationships, ignoring missing targets (unlike manage.py loaddata)
    # fields = dest_model._meta.get_fields_with_model()
    # fk_fields = [(f.name, f.related.parent_model, f.related.field) for (f, m) in fields if isinstance(f, ForeignKey)] 

    try:
        qs = qs.objects
    except:
        pass
    N = qs.count()

    if verbosity:
        print('Loading %r records from the queryset provided...' % N)

    if clear and not dry_run:
        if verbosity:
            print "WARNING: Deleting %d records from %r !!!!!!!" % (dest_model.objects.count(), dest_model)
        dest_model.objects.all().delete()
    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        pbar = pb.ProgressBar(widgets=widgets, maxval=N).start()
    i = 0
    dest_model._meta.get_all
    for d in qs.values():
        if verbosity > 2:
            print(repr(d))
        m = django_object_from_row(d, dest_model)
        if verbosity:
            pbar.update(i)
            i += 1
            if verbosity > 2:
                print m
        if not dry_run:
            m.save()
    if verbosity:
        pbar.finish()


def import_queryset_untested(dest_model, queryset, model_app=None, nullify_pk=True, batch_len=1000, verbosity=1, clear=False, dry_run=False):
    """Import data from one model (queryset) into a different model

    `import_items()` is more than 2x faster, but uses much more RAM (all records loaded into RAM at once?)

    Similar to `manage.py loaddata`, but loads records in batches using `bulk_create()` rather than `.save()`
    `batch_len argument limits the number of records loaded into RAM at once (reducing RAM footprint)
    Each batch typically causes a new query to be issued to the database, thus spreading the CPU load among cores
    `queryset` may be a model name string, a model class, or a queryset returned from by a query

    TODO: allow dest_model to be a queryset of objects to be deleted before the new objects are loaded!
    WARNING: will fail if the primary key field name is different in the source and destination models
    """
    import re

    dest_model = get_model(dest_model, app=model_app)
    if not model_app:
        model_app = dest_model.__module__.split('.')[0].lower()
    model_name = dest_model.__name__.lower()

    queryset = get_queryset(queryset, app=model_app)
    query_app = queryset.model.__module__.split('.')[0].lower()
    query_model_name = queryset.model.__name__.lower()

    try:
        N = queryset.count()
    except:
        N = len(queryset)

    if clear and not dry_run:
        if verbosity:
            print "WARNING: Deleting %d records from %r to make room for %d new records !!!!!!!" % (dest_model.objects.count(), dest_model, N)
        num_deleted = delete_in_batches(dest_model.objects.all())
        if verbosity:
            print "Finished deleting %d records in %r." % (num_deleted, dest_model)


    if verbosity:
        print 'Loading %d objects from %r into %r ...' % (queryset.count(), queryset.model, dest_model)
    # to change the model in a json fixture file:
    # sed -e 's/^\ \"pk\"\:\ \".*\"\,/"pk": null,/g' -i '' *.json
    # sed -e 's/^\ \"model\"\:\ \"sec_sharp_refurb\.refrefurb\"\,/\ \"model\"\:\ "call_center\.refrefurb\"\,/g' -i '' *.json

    re_pk = re.compile(r'^[ ]*"pk"\:\ .*,[ ]*$', re.MULTILINE)
    re_model = re.compile(r'^[ ]*"model"\:\ "'+ query_app +r'\.' + query_model_name + r'\",[ ]*$', re.MULTILINE)

    JSONSerializer = serializers.get_serializer("json")
    jser = JSONSerializer()


    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=N).start()

    for j, partial_qs in enumerate(util.generate_slices(queryset.all(), batch_len=batch_len)):
        js = jser.serialize(partial_qs, indent=1)
        if verbosity > 1:
            print '---------- SOURCE FIXTURE ----------------'
            print js
        if nullify_pk:
            js = re_pk.sub(' "pk": null,', js)
            # FIXME: add the pk values back in as a normal (nonpk) fields within the JSON or the DeserializedObject list
        js = re_model.sub(' "model": "%s.%s",' % (model_app, model_name), js)
        if verbosity > 1:
            print '---------- DESTINATION FIXTURE ----------------'
            print js

        # manage.py loaddata does: 
        # objects = serializers.deserialize('json', <fixture_file_pointer>, using=<database_dbname_from_settings>, ignorenonexistent=ignore)
        # for obj in objects: obj.save()
        new_objects = list(serializers.deserialize("json", js))
        if verbosity:
            print '---------- DESTINATION OBJECTS ----------------'
            print new_objects
        for obj in new_objects:
            obj.pk = i + 1
            i += 1
        dest_model.objects.bulk_create(new_objects)
        if verbosity:
            print '%d objects created. %d total.' % (len(new_objects), dest_model.objects.count())

        # # If you get AttributeError: DeserializedObject has no attrribute "pk"
        # for obj in new_objects:
        #     i += 1
        #     obj.save()

        pbar.update(i)

    pbar.finish()



# def import_qs(src_qs, dest_model,  batch_len=100, db_alias='default', 
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
#     for batch_num, dict_batch in enumerate(util.generate_batches(item_seq, batch_len)):
#         if verbosity > 2:
#             print(repr(dict_batch))
#             print(repr((batch_num, len(dict_batch), batch_len)))
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
#                 len(item_batch), dest_model.__name__, batch_num, int(num_items / float(batch_len)), db_alias))
#         dest_model.objects.bulk_create(item_batch)

def import_json(path, model, batch_len=100, db_alias='default', start_batch=0, end_batch=None, ignore_errors=False, verbosity=2):
    """Read json file (not in django fixture format) and create the appropriate records using the provided database model."""

    # TODO: use a generator to save memory for large json files/databases
    if verbosity:
        print('Reading json records (dictionaries) from {0}.'.format(repr(path)))
    item_list = json.load(open(path, 'r'))
    if verbosity:
        print('Finished reading {0} items from {1}.'.format(len(item_list), repr(path)))
    import_items(item_list, model=model, batch_len=batch_len, db_alias=db_alias, start_batch=start_batch, end_batch=end_batch, ignore_errors=ignore_errors, verbosity=verbosity)


################################################
# These attempt to speed data inserts using bulk_create


def bulk_update(object_list, ignore_errors=False, delete_first=False, verbosity=0):
    '''Bulk_create objects in provided list of model instances, delete database rows for the original pks in the object list.

    Returns any delta in the number of rows in the database table that resulted from the update.
    If nonzero, an error has likely occurred and database integrity is suspect.

    # delete_first = True is required if your model has unique constraints that would be violated by creating duplicate records

    # FIXME: check for unique constraints and raise exception if any exist (won't work because new objects may violate!)
    '''
    if not object_list:
        return 0
    model = object_list[0].__class__
    N_before = model.objects.count()
    pks_to_delete = set()
    for i, obj in enumerate(object_list):
        pks_to_delete.add(obj.pk)
        if delete_first:
            object_list[i] = deepcopy(obj)
        object_list[i].pk = None
    if verbosity > 1:
        print 'Creating %d %r objects.' % (len(object_list), model)
        print 'BEFORE: %d' % model.objects.count()
    if not delete_first:
        model.objects.bulk_create(object_list)
    if verbosity:
        print 'Deleting %d objects with pks: %r ........' % (len(pks_to_delete), pks_to_delete)
    objs_to_delete = model.objects.filter(pk__in=pks_to_delete)
    num_to_delete = objs_to_delete.count()
    if num_to_delete != len(pks_to_delete):
        msg = 'Attempt to delete redundant pks (len %d)! Queryset has count %d. Query was `filter(pk__in=%r). Queryset = %r' % (
            len(pks_to_delete), num_to_delete, pks_to_delete, objs_to_delete)
        if ignore_errors:
            if verbosity:
                print msg
        else:
            raise RuntimeError(msg)
    if verbosity > 1:
        print 'Queryset to delete has %d objects' % objs_to_delete.count()
    objs_to_delete.delete()
    if delete_first:
        model.objects.bulk_create(object_list)
    if verbosity > 1:
        print 'AFTER: %d' % model.objects.count()
    N_after = model.objects.count()
    if ignore_errors:
        if verbosity > 1:
            print 'AFTER: %d' % N_after
    else:
        if N_after != N_before:
            print 'Number of records in %r changed by %d during bulk_create of %r.\n ' % (model, N_after - N_before, object_list)
            msg = 'Records before and after bulk_create are not equal!!! Before=%d, After=%d' % (N_before, N_after)
            raise RuntimeError(msg)
    return N_before - N_after


def generate_queryset_batches(queryset, batch_len=1000, verbosity=1):
    """Filter a queryset by the pk in such a way that no batch is larger than the requested batch_len

    SEE ALSO: pug.nlp.util.generate_slices

    >>> from miner.models import TestModel
    >>> sum(len(list(batch)) for batch in generate_queryset_batches(TestModel, batch_len=7)) == TestModel.objects.count()
    True
    """
    if batch_len == 1:
        for obj in queryset:
            yield obj

    N = queryset.count()

    if not N:
        raise StopIteration("Queryset is empty!")


    if N == 1:
        for obj in queryset:
            yield obj

    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % N, pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=N).start()
    pk_queryset = queryset.filter(pk__isnull=False).values_list('pk', flat=True).order_by('pk')

    N_nonnull = pk_queryset.count()
    N_batches = int(N_nonnull/float(batch_len)) + 1
    
    if verbosity > 1:
        print 'Splitting %d primary_key values (%d nonnull) from %r into %d querysets of size %d or smaller. First loading pks into RAM...' % (N, N_nonnull, queryset.model, N_batches, batch_len)
    nonnull_pk_list = tuple(pk_queryset)
    pk_list = []

    if verbosity > 1:
        print 'Extracting the %d dividing (fencepost) primary keys for use in splitting the querysets with filter queries...' % (N_batches + 1)
    for j in range(N_batches - 1):
        pk_list += [(nonnull_pk_list[j*batch_len], nonnull_pk_list[(j+1)*batch_len - 1])]
    last_batch_len = N_nonnull - (N_batches-1) * batch_len
    pk_list += [(nonnull_pk_list[(N_batches-1) * batch_len], nonnull_pk_list[N-1])]

    if verbosity > 1:
        del(nonnull_pk_list)
        print 'Yielding the %d batches according to the %d dividing (fencepost) primary keys...' % (N_batches, len(pk_list))
    for j in range(N_batches):
        if verbosity:
            pbar.update(i)
        if j < N_batches - 1:
            i += batch_len
        else:
            i += last_batch_len
        # inclusive inequality ensures that even if PKs are repeated they will all be included in the queryset returned
        yield queryset.filter(pk__gte=pk_list[j][0], pk__lte=pk_list[j][1])
    if verbosity:
        pbar.finish()


# def fixture_from_table(table, header_rows=1):
#     """JSON string that represents a valid Django fixture for the data in a table"""
#     yield '[\n'
#     for i in range(header_rows, len(table)):
#         s = fixture_record_from_row(table[i])
#         if i == header_rows:
#             yield s + '\n'
#         else:
#             yield ',\n' + s + '\n'
#     yield ']\n'


def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    A monkey-patch for django.utils.encoding.force_text to robustly handle UTF16
    and latin encodings from non-compliant drivers (myodbc, FreeTDS, some camera EXIF tags).
    Uses pug.nlp.db.clean_utf8 when all other attempts using `six` fail.
 
    Similar to smart_text, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first, saves 30-40% when s is an instance of
    # six.text_type. This function gets called often in that setting.
    if isinstance(s, six.text_type):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if not isinstance(s, six.string_types):
            if hasattr(s, '__unicode__'):
                s = s.__unicode__()
            else:
                if six.PY3:
                    if isinstance(s, bytes):
                        s = six.text_type(s, encoding, errors)
                    else:
                        s = six.text_type(s)
                else:
                    s = six.text_type(bytes(s), encoding, errors)
        else:
            # Note: We use .decode() here, instead of six.text_type(s, encoding,
            # errors), so that if s is a SafeBytes, it ends up being a
            # SafeText at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(s, Exception):
            try:
                s = clean_utf8(s)
            except:
                raise DjangoUnicodeDecodeError(s, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_text(arg, encoding, strings_only,
                    errors) for arg in s])
    return s


def dump_json(model, batch_len=200000, use_natural_keys=True, verbosity=1):
    """Dump database records to .json Django fixture file, one file for each batch of `batch_len` records

    Files are suitable for loading with "python manage.py loaddata folder_name_containing_files/*".
    """
    model = get_model(model)

    N = model.objects.count()

    if verbosity:
        widgets = [pb.Counter(), '/%d rows: ' % (N,), pb.Percentage(), ' ', pb.RotatingMarker(), ' ', pb.Bar(),' ', pb.ETA()]
        i, pbar = 0, pb.ProgressBar(widgets=widgets, maxval=N).start()

    JSONSerializer = serializers.get_serializer("json")
    jser = JSONSerializer()

    if verbosity:
        pbar.update(0)
    for i, partial_qs in enumerate(util.generate_slices(model.objects.all(), batch_len=batch_len)):
        with open(model._meta.app_label.lower() + '--' + model._meta.object_name.lower() + '--%04d.json' % i, 'w') as fpout:
            if verbosity:
                pbar.update(i*batch_len)
            jser.serialize(partial_qs, indent=1, stream=fpout, use_natural_keys=use_natural_keys)
    if verbosity:
        pbar.finish()

