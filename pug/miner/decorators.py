from pug.nlp.db import representation
from inspect import getmodule
import os
import re


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


def represent(cls):
    setattr(cls, '__unicode__', representation)
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


