import sys
import os
import re

from StringIO import StringIO

from django.conf import settings
from django.core.management import call_command

# 1. turn this into a management command `inspectdbs`
# 2. create a Model mixin that stores attributes in the Meta class per this:
#   http://stackoverflow.com/questions/1088431/adding-attributes-into-django-models-meta-class


def inspect_dbs(output_dir='.', db_names=None, db_aliases=None, alias_prefix='SEC_', db_alias_lower=str.lower, verbosity=1):
    db_names = db_names or settings.INSPECT_DB_NAMES
    db_aliases = db_aliases or [alias_prefix + db_alias_lower(name) for name in db_names]
    for db_name, db_alias in zip(db_names, db_aliases):
        fn = os.path.join(os.path.realpath(output_dir), 'models_%s.py' % db_alias)
        if verbosity:
            sys.stderr.write('Writing model definitions to file %r for db_alias %r.\n' % (fn, db_alias))
        models_py_buffer = StringIO()
        call_command('inspectdb', database=db_alias, verbosity=0, traceback=False, interactive=False, stdout=models_py_buffer)
        models_py_buffer.seek(0)
        with open(fn, 'w') as fp:
            line = models_py_buffer.readline()
            while line and fp:
                if verbosity > 2:
                    sys.stderr.write('READ: %r\n' % line)
                seditted_lines = line
                for sed in inspect_dbs.seds:
                    if sed['regex'].match(line):
                        seditted_lines =  sed.get('before', '').format(**{'db_name': db_name, 'alias_prefix': alias_prefix}) or ''
                        seditted_lines += line if sed.get('sub', None) is None else sed['regex'].sub(sed['sub'], line)
                        seditted_lines += sed.get('after', '').format(**{'db_name': db_name, 'alias_prefix': alias_prefix}) or ''
                if verbosity > 2:
                    sys.stderr.write('WRITING: %r\n' % seditted_lines)
                fp.write(seditted_lines)
                line = models_py_buffer.readline()
inspect_dbs.seds = [
    {
        'regex': re.compile(r'^from django[.]\w+\simport\smodels(\s*[#].*)?$'),
        'after': '\nfrom pug.miner import decorators\n',
    },
    {
        'regex': re.compile(r'^class\s+\w+\(models[.]Model\):(\s*[#].*)?$'),
        'before': "\n@decorators.represent\n@decorators.dbname(db_name='{db_name}', alias_prefix='{alias_prefix}')\n",
    },
    {
        'regex': re.compile(r'^(\s+\w+\s*=\s*models[.])AutoField\(\)'),
        'sub': r"\1IntegerField(primary_key=True)",
    }, 
    {
        'regex': re.compile(r'^(\s+\w+\s*=\s*models[.])AutoField\((.+)\)'),
        'sub': r"\1IntegerField(\2)",
    },
    ]
