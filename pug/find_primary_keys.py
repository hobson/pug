from traceback import print_exc

from nlp import db
from django.db import models, connection, connections

from nlp import sqlserver as sql

from collections import OrderedDict

import re
import json

types_not_countable = ('text',)
types_not_aggregatable = ('text', 'bit',)


def clean_utf8(utf8_string):
    r"""Delete any invalid symbols in a UTF-8 encoded string

    Returns the cleaned string.
    
    >>> clean_utf8('A\xffB\xffC ')
    'ABC '
    """
    if isinstance(utf8_string, basestring):
        while True:
            try:
                json.dumps(utf8_string)
                break
            except UnicodeDecodeError as e:
                m = re.match(r".*can't[ ]decode[ ]byte[ ]0x[0-9a-fA-F]{2}[ ]in[ ]position[ ](\d+)[ :.].*", str(e))
                if m and m.group(1):
                    i = int(m.group(1))
                    utf8_string = utf8_string[:i] + utf8_string[i+1:]
                else:
                    raise e
    return utf8_string


def get_cursor_table_names(cursor):
    # connection_string = "Driver=FreeTDS;Server=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=7.2;PORT=%s" % (
    #     settings.DATABASES['ssg']['HOST'],settings.DATABASES['ssg']['NAME'], settings.DATABASES['ssg']['USER'],
    #     settings.DATABASES['ssg']['PASSWORD'],  settings.DATABASES['ssg']['PORT'],
    #     )
    # connection = pyodbc.connect(connection_string, autocommit=True)
    # connection = connections[db_alias]
    # cursor = connection.cursor()
    return [row[-2] for row in cursor.execute("""SELECT * FROM information_schema.tables""").fetchall()]


def inspect_cursor(cursor=None):
    if isinstance(cursor, basestring):
        cursor = connections[cursor].cursor()
    if not cursor:
        cursor = connections['default']
    for table_name in get_cursor_table_names(cursor):
        print table_name

# FIXME: break `inspect_db` into modules that make sense, like:
#   inspect_column()
#   inspect_table()
#   count_values()
#   count_unique()
def inspect_db(app='refurb', db_alias='refurb', table=None, verbosity=2, column=None):
    if app and isinstance(app, basestring):
        app = db.get_app(app)
    model_names = list(mc.__name__ for mc in models.get_models(app))
    meta = OrderedDict()
    for model_name in model_names:
        model = db.get_model(model_name, app=app)
        if table is not None and isinstance(table, basestring):
            if model._meta.db_table != table:
                if verbosity>1:
                    print 'skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        elif callable(table):
            if not table(model._meta.db_table):
                if verbosity>1:
                    print 'skipped model named %s with db table names %s.' % (model_name, model._meta.db_table)
                continue
        meta[model_name] = OrderedDict()
        meta[model_name]['Meta'] = OrderedDict()
        meta[model_name]['Meta']['primary_key'] = None
        meta[model_name]['Meta']['count'] = model.objects.using(db_alias).count()
        meta[model_name]['Meta']['db_table'] = model._meta.db_table
        
        if verbosity>1:
            print '%s.Meta = %r' % (model_name, meta[model_name]['Meta'])
        
        # meta[model_name]['Meta']['db_name'] = db_alias
        properties_of_fields = sql.get_meta_dicts(cursor=db_alias, table=meta[model_name]['Meta']['db_table'])
        field_properties_dict = OrderedDict((field['name'], field) for field in properties_of_fields)
        if verbosity > 1:
            print '-' * 20 + model_name + '-' * 20
        db_primary_keys = [field['name'] for field in properties_of_fields if field['primary_key']]
        if len(db_primary_keys) == 1:
            meta[model_name]['Meta']['primary_key'] = db_primary_keys[0]
        for field in model._meta._fields():
            db_column = field.db_column
            if not db_column:
                if field.name in field_properties_dict:
                    db_column = field.name
                elif field.name.lower() in field_properties_dict:
                    db_column = field.name.lower()
                elif field.name.upper() in field_properties_dict:
                    db_column = field.name.upper()
            if not db_column:
                if verbosity > 1:
                    print "WARNING: Skipped field named '%s'. No column found in the database.table '%s.%s'." % (field.name, db_alias, meta[model_name]['Meta']['db_table'])
                continue
            if column is not None and isinstance(column, basestring):
                if db_column != column:
                    if verbosity>1:
                        print 'Skipped field named %s.%s with db column name %s.%s.' % (model_name, field.name, model._meta.db_table, db_column)
                    continue
            elif callable(column):
                if not column(db_column):
                    if verbosity>1:
                        print 'Skipped field named %s.%s with db column name %s.%s.' % (model_name, field.name, model._meta.db_table, db_column)
                    continue
            if (field.name == 'id' and isinstance(field, models.fields.AutoField)
                    and field.primary_key and (not field_properties_dict[db_column]['primary_key'])):
                continue

            # Calculate the fraction of values in a column that are distinct (unique).
            #   For columns that aren't populated with 100% distinct values, the fraction may help identify columns that are part of a  "unique-together" compound key
            #   Necessary constraint for col1 and col2 to be compound key: col1_uniqueness + col2_uniqueness >= 1.0 (100%)
            # TODO: check for other clues about primary_keyness besides just uniqueness 
            field_properties_dict[db_column]['num_distinct'] = None
            field_properties_dict[db_column]['num_null'] = None
            if field_properties_dict[db_column]['type'] not in types_not_countable:
                field_properties_dict[db_column]['num_distinct'] = model.objects.using(db_alias).values(field.name).distinct().count()
                field_properties_dict[db_column]['num_null'] = model.objects.using(db_alias).filter(**{'%s__isnull' % field.name: True}).count()

            field_properties_dict[db_column]['max'] = None
            field_properties_dict[db_column]['min'] = None
            # check field_properties_dict[db_column]['num_null'] for all Null first?
            if field_properties_dict[db_column]['type'] not in types_not_aggregatable:
                connection.close()
                try:
                    field_properties_dict[db_column]['max'] = clean_utf8(model.objects.using(db_alias).aggregate(max_value=models.Max(field.name))['max_value'])
                    field_properties_dict[db_column]['min'] = clean_utf8(model.objects.using(db_alias).aggregate(min_value=models.Min(field.name))['min_value'])
                except ValueError, e:
                    if verbosity > 1:
                        print_exc()
                        print "ValueError (UnicodeDecodeError?): Skipped max/min calculations for field named '%s' (%s) because of %s." % (field.name, repr(db_column), e)
                    connection.close()
                # validate values that might be invalid strings do to db encoding/decoding errors (make sure they are UTF-8
                for k in ('min', 'max'):
                    clean_utf8(field_properties_dict.get(db_column, {}).get(k))



            # field_properties_dict[db_column]['count'] = N
            if verbosity > 2:
                print '%s (%s) has %s / %s (%3.1f%%) distinct values between %s and %s, excluding %s nulls.' % (field.name, db_column, 
                                                             field_properties_dict[db_column]['num_distinct'], 
                                                             meta[model_name]['Meta']['count'],
                                                             100. * (field_properties_dict[db_column]['num_distinct'] or 0) / (meta[model_name]['Meta']['count'] or 1),
                                                             repr(field_properties_dict[db_column]['min']),
                                                             repr(field_properties_dict[db_column]['max']),
                                                             field_properties_dict[db_column]['num_null'])
            # TODO:
            #   1. count the number of values that are strings that could be converted to
            #      a. integers
            #      b. floats
            #      c. dates / datetimes
            #      d. booleans / nullbooleans
            #      e. other ordinal, categorical, or quantitative types
            #   2. count the number of null values
            #      a. null/None
            #      b. blank
            #      c. whitespace or other strings signifying null ('NULL', 'None', 'N/A', 'NaN', 'Not provided')
        if verbosity > 1:
            print field_properties_dict 
        meta[model_name].update(field_properties_dict)
    return meta


def get_indexes(meta, table_name=None, model_name=None):
    # return a single field_name: infodict pair for the requested table or model
    # format of infodict should be: 
    # { field_name: { 
    #       'primary_key': boolean representing whether it's the primary key,
    #       'unique': boolean representing whether it's a unique index }
    # ... }
    indexes, pk_field = {}, None
    for meta_model_name, model_meta in meta.iteritems():
        if not (table_name == model_meta['Meta']['db_name'] or model_name == meta_model_name):
            continue
        table_name, model_name = model_meta['Meta']['db_name'], meta_model_name
        N = model_meta['Meta'].get('count', 0)
        for field_name, field_meta in model_meta.iteritems():
            if field_name == 'Meta':
                continue
            if field_meta.get('primary_key'):
                # TODO: Allow more than one index per model/table
                return {field_name: {
                    'primary_key': True,
                    'unique': field_meta.get('unique') or (
                        N >= 3 and field_meta.get('num_null') <= 1 and field_meta.get('num_distinct') == N),
                    }}
        score_names = []
        for field_name, field_meta in model_meta.iteritems():
            score = .5 * float(field_meta.get('unique') or (N >= 3 and field_meta.get('num_null') <= 1 and field_meta.get('num_distinct') == N))
            score += .2 * float(field_meta.get('type') == 'numeric')
            score += .1 * float(field_meta.get('type') == 'char')
            score -= .3 * float(field_meta.get('type') == 'text')
            score_names += [(score, field_name)]
        # FIXME
        max_name = max(score_names)
        field_meta = model_meta[max_name[1]]
        return {max_name[1]: {
                'primary_key': True,
                'unique': field_meta.get('unique') or (
                    N >= 3 and field_meta.get('num_null') <= 1 and field_meta.get('num_distinct') == N),
                }}

                    
def models_with_unique_column(meta, exclude_single_pk=True, exclude_multi_pk=True):
    """Return a list of model names for models that have at least 1 field that has all distinct values (could be used as primary_key)"""
    models_with_potential_pk = []
    for model_name, model_fields in meta.iteritems():
        if exclude_single_pk:
            if model_fields['Meta']['primary_key']:
                continue
        if exclude_multi_pk:
            if any(not field['primary_key'] and field['num_distinct'] == 1 for field in model_fields if field is not 'Meta'):
                models_with_potential_pk += model_name
        else:
            if any(field['num_distinct'] == 1 for field in model_fields if field is not 'Meta'):
                models_with_potential_pk += model_name
    return models_with_potential_pk