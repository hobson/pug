"""Function and class decorators for memoizing and logging or adding methods to a Django Model.

Shamelessly borrowed from python.org:
https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
https://wiki.python.org/moin/PythonDecoratorLibrary#Logging_decorator_with_specified_logger_.28or_default.29
"""

import os
import re
import collections
import functools
import logging
from types import NoneType

from nlp.db import representation
from inspect import getmodule
from nlp.util import make_name
# from django.db.models.fields.related import RelatedField
# from django.conf import settings
#from exceptions import TypeError

def force_hashable(obj, recursive=True):
    """Force frozenset() command to freeze the order and contents of multables and iterables like lists, dicts, generators

    Useful for memoization and constructing dicts or hashtables where keys must be immutable.

    >>> force_hashable([1,2.,['3']])
    (1, 2.0, ('3',))    
    >>> force_hashable(i for i in range(3))
    (1, 2, 3)
    >>> from collections import Counter
    >>> force_hashable(Counter('abbccc')) ==  (('a', 1), ('c', 3), ('b', 2))
    True
    """
    try:
        hash(obj)
        return obj
    except:
        if hasattr(obj, '__iter__'):
            # looks like a Mapping if it has .get() and .items(), so should treat it like one
            if hasattr(obj, 'get') and hasattr(obj, 'items'):
                # tuples don't have an 'items' method so this should recurse forever
                return force_hashable(tuple(obj.items()))
            if recursive:
                return tuple(force_hashable(item) for item in obj)
            return tuple(obj)
    # strings are hashable so this ends the recursion
    return unicode(obj)


def force_frozenset(obj):
    """Force frozenset() command to freeze the order and contents of multables and iterables like lists, dicts, generators

    Useful for memoization and constructing dicts or hashtables where keys must be immutable
    """ 
    # make it a set/tuple of 1 if it is a scalar and not a set already
    return tuple(force_hashable(obj))


class memoize(object):
    '''Decorator to caches a function's return value
    If called later with any set of arguments previously used,
    the cached value is returned and the function is not reevaluated,
    saving execution time.

    https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize

    hobs added kwargs per http://stackoverflow.com/a/6408175/623735
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args, **kwargs):
        cache_key = (force_hashable(args), force_hashable(kwargs.items()))
        if cache_key in self.cache:
            return self.cache[cache_key]
        else:
            value = self.func(*args, **kwargs)
            self.cache[cache_key] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class log_with(object):
    '''Logging decorator that allows you to specify a specific logger.

    https://wiki.python.org/moin/PythonDecoratorLibrary#Logging_decorator_with_specified_logger_.28or_default.29
    '''
    # Customize these messages
    ENTRY_MESSAGE = 'Entering {}'
    EXIT_MESSAGE = 'Exiting {}'

    def __init__(self, logger=None):
        self.logger = logger

    def __call__(self, func):
        '''Returns a wrapper that wraps func.
        The wrapper will log the entry and exit points of the function
        with logging.INFO level.
        '''

        # set logger if it was not set earlier
        if not self.logger:
            logging.basicConfig()
            self.logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwds):
            self.logger.info(self.ENTRY_MESSAGE.format(func.__name__))  # logging level .info(). Set to .debug() if you want to
            f_result = func(*args, **kwds)
            self.logger.info(self.EXIT_MESSAGE.format(func.__name__))   # logging level .info(). Set to .debug() if you want to
            return f_result
        return wrapper


class dbname(object):
    'Decorator to add _db_name and _db_alias attributes to a class definition (typically a django Model)'

    def __init__(self, db_name=None, alias_prefix=''):
        self.db_name = db_name
        self.alias_prefix = alias_prefix or ''

    def __call__(self, cls):
        if not self.db_name:
            self.db_name = os.path.basename(getmodule(cls).__file__)
            self.db_name = re.sub(r'[.]pyc?$', '', self.db_name, flags=re.IGNORECASE)
            self.db_name = re.sub(r'[._-]+models$', '', self.db_name, flags=re.IGNORECASE)
            self.db_name = re.sub(r'^models[._-]+', '', self.db_name, flags=re.IGNORECASE)
        setattr(cls, '_db_alias', self.alias_prefix + self.db_name.lower())    
        setattr(cls, '_db_name', self.db_name)
        return cls


class dbname_from_filename(dbname):
    'Decorator to add _db_name and _db_alias attributes to a class definition'

    def __init__(self, alias_prefix=''):
        super(dbname_from_filename, self).__init__(alias_prefix=alias_prefix)

    def __call__(self, cls):
        if not self.db_name:
            self.db_name = os.path.basename(getmodule(cls).__file__)
            self.db_name = re.sub(r'[.]pyc?$', '', self.db_name, flags=re.IGNORECASE)
            self.db_name = re.sub(r'[._-]+models$', '', self.db_name, flags=re.IGNORECASE)
            self.db_name = re.sub(r'^models[._-]+', '', self.db_name, flags=re.IGNORECASE)
        setattr(cls, '_db_alias', self.alias_prefix + self.db_name.lower())    
        setattr(cls, '_db_name', self.db_name)
        return cls


class prefix_model_name_with_filename(object):
    "DOESNT WORK: Decorator to prefix the class __name__ with the *.py file name."

    def __init__(self, sep=None, remove_prefix=None):
        self.sep = sep or ''
        self.remove_prefix = remove_prefix or 'models_'

    def __call__(self, cls):
        model_name= os.path.basename(getmodule(cls).__file__).split('.')[0]
        kwargs = make_name.DJANGO_MODEL
        kwargs['remove_prefix'] = self.remove_prefix
        model_name = make_name(model_name, **kwargs)
        # self.db_name = re.sub(r'[.]pyc?$', '', self.db_name, flags=re.IGNORECASE)
        # self.db_name = re.sub(r'[._-]+models$', '', self.db_name, flags=re.IGNORECASE)
        # self.db_name = re.sub(r'^models[._-]+', '', self.db_name, flags=re.IGNORECASE)
        setattr(cls, '__name__', model_name + self.sep + getattr(cls, '__name__'))
        return cls

# import django_filters
# import django.db.models.fields as django_field_types

# filter_field_type = {
#     django_field_types.IntegerField: django_filters.NumberFilter,
#     django_field_types.FloatField: django_filters.NumberFilter,
#     django_field_types.DecimalField: django_filters.NumberFilter,
#     django_field_types.CharField: django_filters.CharFilter,
#     django_field_types.TextField: django_filters.CharFilter,
#     django_field_types.BooleanField: django_filters.BooleanFilter,
#     django_field_types.NullBooleanField: django_filters.BooleanFilter,
#     #django_field_types.DateField: django_filters.DateFilter,
#     django_field_types.DateTimeField: django_filters.DateTimeFilter,
#     }
# # TODO: different subsets of these within each of the filter types above
# filter_suffixes = ('lt', 'lte', 'gt', 'gte') #, 'startswith', 'istartswith', 'endswith', 'iendswith', 'year', 'month', 'week_day', 'isnull')

# class add_model_field_filters(object):
#     "DOESNT WORK: Decorator to prefix the class __name__ with the *.py file name."

#     def __init__(self, sep=None, remove_prefix=None):
#         self.sep = sep or ''
#         self.remove_prefix = remove_prefix or 'models_'

#     def __call__(self, cls):
#         model_name= os.path.basename(getmodule(cls).__file__).split('.')[0]
#         kwargs = make_name.DJANGO_MODEL
#         kwargs['remove_prefix'] = self.remove_prefix
#         model_name = make_name(model_name, **kwargs)
#         # self.db_name = re.sub(r'[.]pyc?$', '', self.db_name, flags=re.IGNORECASE)
#         # self.db_name = re.sub(r'[._-]+models$', '', self.db_name, flags=re.IGNORECASE)
#         # self.db_name = re.sub(r'^models[._-]+', '', self.db_name, flags=re.IGNORECASE)
#         setattr(cls, '__name__', model_name + self.sep + getattr(cls, '__name__'))
#         for field in cls._meta.model._meta.fields:
#             print field
#             for django_type, filter_type in filter_field_type.iteritems():
#                 #print isinstance(field, django_type)
#                 #print field, django_type
#                 if isinstance(field, django_type):
#                     for suffix in filter_suffixes:
#                         #print field.name + '_' + suffix, '|', repr(filter_type(name=field.name, lookup_type=suffix))
#                         setattr(cls, field.name + '_' + suffix, filter_type(name=field.name, lookup_type=suffix))
#         return cls

# http://stackoverflow.com/a/21863400/623735
# def cls_changer(name, parents, attrs):
#     model_name = os.path.basename(__file__).split('.')[0]
#     res = type(model_name+name, parents, attrs)
#     gl = globals()
#     gl[model_name+name] = res
#     return res

# class ShipMeth(object):
#     __metaclass__ = cls_changer
#     ship_meth = models.CharField(max_length=1, primary_key=True)
#     description = models.CharField(max_length=20, blank=True)
#     charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
#     def_field = models.CharField(max_length=1, db_column='def', blank=True) # Field renamed because it was a Python reserved word.
#     charge_net = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
#     charge_shipping = models.CharField(max_length=1, blank=True)
#     ship_cost1 = models.DecimalField(null=True, max_digits=18, decimal_places=0, blank=True)
#     ship_cost2 = models.DecimalField(null=True, max_digits=18, decimal_places=0, blank=True)



def represent(cls):
    setattr(cls, '__unicode__', representation)
    return cls

# FIXME, DRY these 3 models up by just adding a kwarg to select between the 2 decorators
#        very unDRY (only a few characters changed in each!)
def _link_rels(obj, fields=None, save=False, overwrite=False):
    """Populate any database related fields (ForeignKeyField, OneToOneField) that have `_get`ters to populate them with"""
    if not fields:
        meta = obj._meta
        fields = [f.name for f in meta.fields if hasattr(f, 'do_related_class') and not f.primary_key and hasattr(meta, '_get_' + f.name) and hasattr(meta, '_' + f.name)]
    for field in fields:
        # skip fields if they contain non-null data and `overwrite` option wasn't set
        if not overwrite and not isinstance(getattr(obj, field, None), NoneType):
            # print 'skipping %s which already has a value of %s' % (field, getattr(obj, field, None))
            continue
        if hasattr(obj, field):
            setattr(obj, field, getattr(obj, '_' + field, None))
    if save:
        obj.save()
    return obj

def _denormalize(obj, fields=None, save=False, overwrite=False):
    """Update/populate any database fields that are not related fields (FKs) but have `_get`ters to populate them with"""
    if not fields:
        meta = obj._meta
        fields = [f.name for f in meta.fields if not hasattr(f, 'do_related_class') and not f.primary_key and hasattr(meta, '_get_' + f.name) and hasattr(meta, '_' + f.name)]
    for field in fields:
        # skip fields if they contain non-null data and `overwrite` option wasn't set
        if not overwrite and not isinstance(getattr(obj, field, None), NoneType):
            # print 'skipping %s which already has a value of %s' % (field, getattr(obj, field, None))
            continue
        if hasattr(obj, field):
            setattr(obj, field, getattr(obj, '_' + field, None))
    if save:
        obj.save()
    return obj

def _update(obj, fields=None, save=False, overwrite=False):
    """Update/populate any database fields that have `_get`ters to populate them with, regardless of whether they are data fields or related fields"""
    if not fields:
        meta = obj._meta
        fields = [f.name for f in meta.fields if not f.primary_key and hasattr(meta, '_get_' + f.name) and hasattr(meta, '_' + f.name)]
    # print fields
    fields_updated = []
    for field in fields:
        # skip fields if they contain non-null data and `overwrite` option wasn't set
        if not overwrite and not getattr(obj, field, None) == None:
            # print 'skipping %s which already has a value of %s' % (field, getattr(obj, field, None))
            continue
        # print field
        if hasattr(obj, field):
            # print field, getattr(obj, '_' + field, None)
            setattr(obj, field, getattr(obj, '_' + field, None))
            if getattr(obj, field, None) != None:
                fields_updated += [field]
    if save:
        obj.save()
    return fields_updated

# TODO: make this a decotator class that accepts arguments which become default args of the link_rels method (fields, overwrite, save)
def linkable_rels(cls):
    fields = tuple(f.name for f in cls._meta.fields if isinstance(f, RelatedField) and hasattr(cls, '_get_' + f.name) and hasattr(cls, '_' + f.name))
    # FIXME: instantiate a new copy of the _link_rels function and give it default arguments
    def _customized_link_rels(obj, fields=fields, save=False, overwrite=False):
        return _link_rels(obj, fields=fields, save=save, overwrite=overwrite)
    setattr(cls, '_link_rels', _customized_link_rels)
    return cls


# TODO: make this a decotator class that accepts arguments which become default args of the link_rels method (fields, overwrite, save)
def updatable(cls):
    fields = tuple(f.name for f in cls._meta.fields if not f.primary_key and hasattr(cls, '_get_' + f.name) and hasattr(cls, '_' + f.name))
    # FIXME: instantiate a new copy of the _link_rels function and give it default arguments
    def _customized_update(obj, fields=fields, save=False, overwrite=False):
        return _update(obj, fields=fields, save=save, overwrite=overwrite)
    setattr(cls, '_update', _customized_update)
    return cls


def audit(cls):
    setattr(cls, 'updated', models.DateTimeField(auto_now=True))
    setattr(cls, 'created', models.DateTimeField(auto_now_add=True))
    return cls


# class dbname(object):
#     'Decorator to add _db_name and _db_alias attributes to a class definition'

#     def __init__(self, arg1, arg2, arg3):
#         """
#         If there are decorator arguments, the function
#         to be decorated is not passed to the constructor!
#         """
#         print "Inside __init__()"
#         self.arg1 = arg1
#         self.arg2 = arg2
#         self.arg3 = arg3

#     def __call__(self, f):
#         """
#         If there are decorator arguments, __call__() is only called
#         once, as part of the decoration process! You can only give
#         it a single argument, which is the function object.
#         """
#         print "Inside __call__()"
#         def wrapped_f(*args):
#             print "Inside wrapped_f()"
#             print "Decorator arguments:", self.arg1, self.arg2, self.arg3
#             f(*args)
#             print "After f(*args)"
#         return wrapped_f


