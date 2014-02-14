from pug.nlp.db import representation
from inspect import getmodule
import os
import re


def dbname_from_filename(cls, db_name='', alias_prefix=''):
    if not db_name:
        db_name = os.path.basename(getmodule(cls).__file__)
        db_name = re.sub(r'[.]pyc?$', '', flags=re.IGNORECASE)
        db_name = re.sub(r'[._-]+models$', '', flags=re.IGNORECASE)
        db_name = re.sub(r'^models[._-]+', '', flags=re.IGNORECASE)
    setattr(cls, '_db_alias', alias_prefix + db_name.lower())    
    setattr(cls, '_db_name', db_name)
    return cls    

def represent(cls):
    setattr(cls, '__unicode__', representation)
    return cls
