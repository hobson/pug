"""Function decorators for memoizing and logging.

Shamelessly borrowed from python.org:
https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
https://wiki.python.org/moin/PythonDecoratorLibrary#Logging_decorator_with_specified_logger_.28or_default.29
"""

import os
import re
import collections
import functools
import logging

from nlp.db import representation
from inspect import getmodule
from nlp.util import make_name


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
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args, **kwargs)
        cache_key = (args, frozenset(kwargs.items()))
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
    'Decorator to add _db_name and _db_alias attributes to a class definition'

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

def _link_rels(obj, fields=(), save=False, overwrite=False):
    for field in fields:
        if not overwrite and getattr(obj, field.lower(), None):
            continue
        if hasattr(obj, field):
            setattr(obj, field, getattr(obj, '_' + field, None))
    if save:
        obj.save()

def add_link_rels(cls):
    setattr(cls, '_link_rel', _link_rels)
    setattr(cls, '_link_rels', _link_rels)
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


