from __future__ import unicode_literals

import keyword
import re
from optparse import make_option
import fnmatch
import json

import pyodbc

from django.db import connections
#from django.conf import settings
#from django.utils import six

from django.core.management.commands.inspectdb import Command as InspectDBCommand
from pug.db.explore import db_meta, get_indexes
from pug.db.sqlserver import get_meta_tuples
from pug.nlp.db import clean_utf8




connection = pyodbc.connect('Driver=FreeTDS;Server=SERVERNAME;DATABASE=DBNAME;UID=UNAME;PWD=CATCHMEIFYOUCAN;TDS_Version=7.2;PORT=1433')
#         >>> cursor = connection.cursor()

def callable_table_name_filter(table_name, filter_string=None, lowercase=True):
    if filter_string is None:
        filter_string = callable_table_name_filter.filter_string
    # is the filter a glob expression (rather than a compiled regex)?
    if isinstance(filter_string, basestring):
        if lowercase:
            filter_string = filter_string.lower()
        if any(c in filter_string for c in ('[', '*', '?')):
            filter_string = re.compile(fnmatch.translate(filter_string))
        else:
            if table_name == filter_string:
                return True
            # print '%r != %r' % (table_name, filter_string)
            return False
    if filter_string.match(table_name):
        return True
    # print 'no match for %r and %r' % (table_name, filter_string)
    return False
callable_table_name_filter.filter_string = re.compile(r'[a-zA-Z_@#]+')  # valid characters in MS Sql Server Compatability Level 100, unicode characters are also allowed, but not by this regex


#TODO: override django.core.management.commands.Command
class Command(InspectDBCommand):
    help = "Introspects the given MS SQL Database and outputs a fully function Django models.py (with primary_keys defined) string to stdout."

    option_list = InspectDBCommand.option_list + (
        #make_option('--database', action='store', dest='database',
        #    default=DEFAULT_DB_ALIAS, help='Nominates a database to '
        #        'introspect.  Defaults to using the "default" database.'),
        # make_option('--table', action='store', dest='table',
        #     default=None, help='Table to compose model for (default = all).'),
        # make the stealth option explicit and accessible from the command-line
        make_option('--table_name_filter', action='store', dest='table_name_filter',
            default=None, help='Table to compose model for (default = all).'),
        make_option('--app', action='store', dest='app',
            default='crawler', help='App name to examine and compose data model for (default = all).'),
        # make_option('--extra', action='store_true', dest='extra',
        #     default=None, help='Whether to to use custom MS SQL to get extra meta data about tables and fields.'),
    )

    def handle_inspection(self, options):
        verbosity = options.get('verbosity')
        app = options.get('app')

        connection = connections[options.get('database')]
        # use_extra = connections[options.get('extra')]

        # 'table_name_filter' is a stealth option -- callable that returns True if table name should be processed
        table_name_filter = options.get('table_name_filter')
        if table_name_filter is not None and isinstance(table_name_filter, basestring):
            callable_table_name_filter.filter_string = table_name_filter 
            table_name_filter = callable_table_name_filter
            # because the parent method checks the stealth option
            options['table_name_filter'] = table_name_filter

        meta = db_meta(app=app, table=table_name_filter, verbosity=int(verbosity))

        if verbosity > 1:
            print meta
        # 'one_table_name' is a new NONstealth option -- string that indicates the one table (or model) that *should* be processed
        #one_table_name = options.get('table')

        table2model = lambda table_name: table_name.title().replace('_', '').replace(' ', '').replace('-', '')
        strip_prefix = lambda s: s.startswith("u'") and s[1:] or s

        cursor = connection.cursor()
        yield "# This is an auto-generated Django model module."
        yield "# You'll have to do the following manually to clean this up:"
        yield "#     * Rearrange models' order"
        yield "#     * Make sure each model has one field with primary_key=True"
        yield "# Feel free to rename the models, but don't rename db_table values or field names."
        yield "#"
        yield "# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'"
        yield "# into your database."
        yield "from __future__ import unicode_literals"
        yield ''
        yield 'from %s import models' % self.db_module
        yield ''
        known_models = []
        print meta.keys()
        print json.dumps(meta, indent=2)
        for table_name in connection.introspection.table_names(cursor):
            if table_name_filter is not None and callable(table_name_filter):
                if not table_name_filter(table_name):
                    continue
            # if one_table_name is not None and (table_name != one_table_name and table2model(table_name) != one_table_name):
            #     continue
            yield 'class %s(models.Model):' % table2model(table_name)
            known_models.append(table2model(table_name))
            try:
                relations = connection.introspection.get_relations(cursor, table_name)
            except NotImplementedError:
                relations = {}
            try:
                indexes = connection.introspection.get_indexes(cursor, table_name)
            except NotImplementedError:
                indexes = get_indexes(meta, table_name)
            used_column_names = [] # Holds column names used in the table so far
            table_columns = connection.introspection.get_table_description(cursor, table_name)
            table_meta = get_meta_tuples(cursor, table_name)
            for i, (row, extra_meta) in enumerate(zip(table_columns, table_meta)):
                #print i
                #print row
                #print extra_meta
                comment_notes = [] # Holds Field notes, to be displayed in a Python comment.
                extra_params = {}  # Holds Field parameters such as 'db_column'.
                column_name = row[0]
                is_relation = i in relations

                att_name, params, notes = self.normalize_col_name(
                    column_name, used_column_names, is_relation)
                extra_params.update(params)
                comment_notes.extend(notes)

                used_column_names.append(att_name)

                # Add primary_key and unique, if necessary.
                if column_name in indexes:
                    if indexes[column_name]['primary_key']:
                        extra_params['primary_key'] = True
                    elif indexes[column_name]['unique']:
                        extra_params['unique'] = True

                if is_relation:
                    rel_to = relations[i][1] == table_name and "'self'" or table2model(relations[i][1])
                    if rel_to in known_models:
                        field_type = 'ForeignKey(%s' % rel_to
                    else:
                        field_type = "ForeignKey('%s'" % rel_to
                else:
                    # Calling `get_field_type` to get the field type string and any
                    # additional paramters and notes.
                    field_type, field_params, field_notes = self.get_field_type(connection, table_name, row)
                    extra_params.update(field_params)
                    comment_notes.extend(field_notes)

                    field_type += '('

                # Don't output 'id = meta.AutoField(primary_key=True)', because
                # that's assumed if it doesn't exist.
                if att_name == 'id' and field_type == 'AutoField(' and extra_params == {'primary_key': True}:
                    continue

                # Add 'null' and 'blank', if the 'null_ok' flag was present in the
                # table description.
                if row[6]: # If it's NULL...
                    extra_params['blank'] = True
                    if not field_type in ('TextField(', 'CharField('):
                        extra_params['null'] = True

                field_desc = '%s = models.%s' % (att_name, field_type)
                if extra_params:
                    if not field_desc.endswith('('):
                        field_desc += ', '
                    field_desc += ', '.join([
                        '%s=%s' % (k, strip_prefix(repr(v)))
                        for k, v in extra_params.items()])
                field_desc += ')'
                if comment_notes:
                    field_desc += ' # ' + ' '.join(comment_notes)
                yield '    %s' % field_desc
            for meta_line in self.get_meta(table_name):
                yield meta_line

    def normalize_col_name(self, col_name, used_column_names, is_relation):
        """
        Modify the column name to make it Python-compatible as a field name
        """
        field_params = {}
        field_notes = []

        new_name = clean_utf8(col_name)
        new_name = col_name.lower()
        if new_name != col_name:
            field_notes.append('Field name made lowercase.')

        if is_relation:
            if new_name.endswith('_id'):
                new_name = new_name[:-3]
            else:
                field_params['db_column'] = col_name

        new_name, num_repl = re.subn(r'\W', '_', new_name)
        if num_repl > 0:
            field_notes.append('Field renamed to remove unsuitable characters.')

        if new_name.find('__') >= 0:
            while new_name.find('__') >= 0:
                new_name = new_name.replace('__', '_')
            if col_name.lower().find('__') >= 0:
                # Only add the comment if the double underscore was in the original name
                field_notes.append("Field renamed because it contained more than one '_' in a row.")

        if new_name.startswith('_'):
            new_name = 'field%s' % new_name
            field_notes.append("Field renamed because it started with '_'.")

        if new_name.endswith('_'):
            new_name = '%sfield' % new_name
            field_notes.append("Field renamed because it ended with '_'.")

        if keyword.iskeyword(new_name):
            new_name += '_field'
            field_notes.append('Field renamed because it was a Python reserved word.')

        if new_name[0].isdigit():
            new_name = 'number_%s' % new_name
            field_notes.append("Field renamed because it wasn't a valid Python identifier.")

        if new_name in used_column_names:
            num = 0
            while '%s_%d' % (new_name, num) in used_column_names:
                num += 1
            new_name = '%s_%d' % (new_name, num)
            field_notes.append('Field renamed because of name conflict.')

        if col_name != new_name and field_notes:
            field_params['db_column'] = col_name

        return new_name, field_params, field_notes

    def get_field_type(self, connection, table_name, row):
        """
        Given the database connection, the table name, and the cursor row
        description, this routine will return the given field type name, as
        well as any additional keyword parameters and notes for the field.
        """
        field_params = {}
        field_notes = []

        try:
            field_type = connection.introspection.get_field_type(row[1], row)
        except KeyError:
            field_type = 'TextField'
            field_notes.append('This field type is a guess.')

        # This is a hook for DATA_TYPES_REVERSE to return a tuple of
        # (field_type, field_params_dict).
        if type(field_type) is tuple:
            field_type, new_params = field_type
            field_params.update(new_params)

        # Add max_length for all CharFields.
        if field_type == 'CharField' and row[3]:
            field_params['max_length'] = row[3]

        if field_type == 'DecimalField':
            field_params['max_digits'] = row[4]
            field_params['decimal_places'] = row[5]

        return field_type, field_params, field_notes

    def get_meta(self, table_name):
        """
        Return a sequence comprising the lines of code necessary
        to construct the inner Meta class for the model corresponding
        to the given database table name.
        """
        return ["    class Meta:",
                "        db_table = '%s'" % table_name,
                ""]
