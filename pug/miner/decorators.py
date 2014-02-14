from pug.nlp.db import representation
from inspect import getmodule
import os


def dbname_from_filename(cls):
    fn = os.path.basename(getmodule(cls).__file__)
    fn = fn[:-4] if fn.endswith('.pyc') else fn
    fn = fn[:-3] if fn.endswith('.py') else fn
    fn = fn[:-7] if fn.endswith('_models') else fn
    fn = fn[7:] if fn.startswith('models_') else fn
    setattr(cls, '_db_alias', 'SEC_' + fn.lower())    
    setattr(cls, '_db_name', fn)
    return cls    

def represent(cls):
    setattr(cls, '__unicode__', representation)
    return cls
