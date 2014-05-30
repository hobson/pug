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
                        if verbosity > 1:
                            print 'WAS: %r' % line
                            print ' IS: %r' % seditted_lines
                        break;  # stop processing the regexes if one already matched this line
                if verbosity > 2:
                    sys.stderr.write('WRITING: %r\n' % seditted_lines)
                # TODO: Add a multi-line edit that deals with multiple primary_key=True fields
                #       * delete second and subsequent primary_key=True arguments within the same Model
                #       * add a unique_together constraint on all the primary_keys that were originally there
                fp.write(seditted_lines)
                line = models_py_buffer.readline()
inspect_dbs.seds = [
    {
        'regex': re.compile(r'^from django[.]\w+\simport\smodels(\s*[#].*)?$'),
        'after': '\nfrom pug import decorators\n',
    },
    {
        'regex': re.compile(r'^class\s+\w+\(models[.]Model\):(\s*[#].*)?$'),
        'before': "\n@decorators.represent\n@decorators.dbname(db_name='{db_name}', alias_prefix='{alias_prefix}')\n",
    },
    {
        'regex': re.compile(r'^(\s+\w+\s*=\s*models[.])AutoField\(\)'),
        'sub': r"\1IntegerField(primary_key=True)",
    },  
    { # not strictly necessary, but since this is intended for read-only databases, probably a good idea to change AutoFields to IntegerFields, even if already a primary_key
        'regex': re.compile(r'^(\s+\w+\s*=\s*models[.])AutoField\((.*)(primary_key\=True)(.*)\)'),
        'sub': r"\1IntegerField(\2\3\4)",
    },
    { # any AutoFields not yet turned to IntegerFields need to have their primary_key set
        'regex': re.compile(r'^(\s+\w+\s*=\s*models[.])AutoField\((.+)\)'),
        'sub': r"\1IntegerField(\2, primary_key=True)",
    },
    {
        'regex': re.compile(r'^(\s+\w+\s*=\s*models[.])BooleanField\((.+)\)'),
        'sub': r"\1NullBooleanField(\2)",
    },
    { # no need to do anything if a primary_key argument is set
        'regex': re.compile(r'^\s+id\s*=\s*models[.]\w+Field\(.*primary_key\=True.*\)'),
    },
    { # need to set primary_key if not set for fields named id
        'regex': re.compile(r'^(\s+)id(\s*=\s*models[.]\w+)Field\((.*)\)'),
        'sub': r"\1id\2Field(\3, primary_key=True)",
    },
    ]
