from __future__ import unicode_literals

import keyword
import re
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from pug.db.explore import db_meta, clean_utf8, RobustEncoder
import json

datetime_format = '%Y-%m-%d %H:%M:%S'  # plus timezone name at the end

import datetime
decode_datetime = lambda x: datetime.strptime(x, json.datetime_format)


class Command(NoArgsCommand):
    help = "Introspects the database tables in the given Microsoft (SQL Server 2000-2012) database and outputs a Django models.py string to stdout."

    option_list = NoArgsCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to '
                'introspect.  Defaults to using the "default" database.'),
        make_option('--table', action='store', dest='table',
            default=None, help='Table to compose model for (default = all).'),
        make_option('--app', action='store', dest='app',
            default='crawler', help='App name to examine and compose data model for (default = all).'),
        # make_option('--extra', action='store_true', dest='extra',
        #     default=None, help='Whether to to use custom MS SQL to get extra meta data about tables and fields.'),
    )

    requires_model_validation = False

    db_module = 'django.db'

    def handle_noargs(self, **options):
        try:
            for line in self.handle_inspection(options):
                self.stdout.write("%s\n" % line)
        except NotImplementedError:
            raise CommandError("Database inspection isn't supported for the currently selected database backend.")

    def handle_inspection(self, options):
        one_table = options.get('table')
        verbosity = int(options.get('verbosity'))
        app = options.get('app')
        meta = db_meta(app=app, db_alias=None, table=one_table, verbosity=verbosity)

        # meta is a dict of dicts of dicts, so doesn't iterate easily
        for line in json.dumps(meta, indent=4, cls=RobustEncoder).split('\n'):
            yield line

    def normalize_col_name(self, col_name, used_column_names, is_relation):
        """
        Modify the column name to make it Python-compatible as a field name
        """
        field_params = {}
        field_notes = []

        new_name = clean_utf8(col_name)
        new_name = new_name.lower()
        if new_name != col_name:
            field_notes.append('Field name cleaned of non-UTF-8 bytes and cast to lowercase.')

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
