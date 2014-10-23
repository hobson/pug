import datetime

from django.db import models

#from django_hstore import hstore
from jsonfield import JSONField

from pug.nlp.db import representation
# FIXME: simplify circular import/dependencies with miner app 
#from pug.miner import explore
from model_mixin import DateMixin


class Connection(models.Model):
    "The username, password, IP Address or URL required to access a database"
    _IMPORTANT_FIELDS = ('pk', 'uri', 'user')

    ip       = models.CharField(max_length=15, null=True)
    uri      = models.TextField(null=True)
    fqdn     = models.TextField(null=True)
    user     = models.TextField(null=True)
    password = models.TextField(null=True)
    port     = models.IntegerField(null=False)

    def __unicode__(self):
        return representation(self)


class AggregatedResults(DateMixin):
    """Storage a results json string that was returned by any restful web-based service

    DateMixin adds the fields 'updated' and 'created'.

    """
    name           = models.TextField(default='', blank=False)
    slug           = models.TextField(default='', blank=False)
    uri            = models.URLField(help_text='Base service URI without the GET API query')
    get_dict       = JSONField(
        help_text='Complete GET Request URI')
    filter_dict    = JSONField(
        help_text='The query `filter()` portion of the GET Request URI formatted in a form acceptable as a `queryset.filter(**filter_dict)`')
    exclude_dict   = JSONField(
        help_text='The query `exclude()` portion of the GET Request URI formatted in a form evaluated as a `for k, v in exclude_dict.items():  queryset = queryset.exclude({k,v});`')
    results        = JSONField(
        help_text="The dictionary of data used to display the Queries summary table at the top of the Quick Table with aggregate statistics 'mean' (lag), 'num_matches', 'num_returns', 'num_sales', 'effective_return_rate', 'word_match_rate', 'mura_match_rate', 'nprb_match_rate', 'last_update', 'num_mura_match', 'num_word_match', 'num_nprb_match'")
class Database(models.Model):
    """Metadata about a Database (postgres or Microsoft SQL "USE" argument)"""
    _IMPORTANT_FIELDS = ('pk', 'name', 'date')

    name = models.CharField(max_length=128, null=False, default='')
    date = models.DateTimeField(help_text='Timestamp when the metadata was calculated', auto_now_add=True, default=datetime.datetime.now, null=False)
    connection = models.ForeignKey(Connection, null=True, default=None)

    __unicode__ = representation


class Table(models.Model):
    """Metadata about a Database table and its Django model"""
    _IMPORTANT_FIELDS = ('pk', 'django_model', 'db_table', 'count')

    app          = models.CharField(max_length=256, default='', null=False, blank=True)
    database     = models.ForeignKey(Database, default=None)
    db_table     = models.CharField(max_length=256, null=True)
    django_model = models.CharField(max_length=256, null=True, default=None)
    primary_key  = models.OneToOneField('Field', null=True, default=None)
    count        = models.IntegerField(null=True, default=None)

    __unicode__ = representation


class ChangeLog(models.Model):
    '''Log of hash of `.values()` of records in any database.table (app.model)

    Used to track changes to tables across databases.
    Facilitates mirroring across databases.
    '''
    model = models.CharField(max_length=255, default='', null=False, blank=True)
    app = models.CharField(max_length=255, default='', null=False, blank=True)
    primary_key = models.IntegerField(default=None, null=True)
    values_hash = models.IntegerField(db_index=True, help_text='Integer hash of a tuple of all of the fields, hash(tuple(record.values_list())), for the source data record.', default=None, null=True, blank=True)


class Type(models.Model):
    FIND_DJANGO_TYPE = {
        'Integer': 'IntegerField',
        'long': 'IntegerField',
        'LONG': 'IntegerField',
        'int': 'IntegerField',
        'INT': 'IntegerField',
        'float': 'FloatField',
        'Float': 'FloatField',
        'double': 'FloatField',
        'Double': 'FloatField',
        'char': 'CharField',
        'str': 'CharField',
        'CHAR': 'CharField',
        'STR': 'CharField',
        'string': 'CharField',
        'STRING': 'CharField',
        'text': 'TextField',
        'TEXT': 'TextField',
        '23': '',
        '1043': '',
        '21': '',
        '23': '',
        '25': '',
        '701': '',
        '1043': '',
        '1184': '',
        '1700': '',
        'boolean': 'NullBooleanField',
        'decimal': 'DecimalField',
        'Decimal': 'DecimalField',
        'DECIMAL': 'DecimalField',
        'VARCHAR': 'CharField', 
        'NCHAR': 'CharField', 
        'NVARCHAR': 'CharField',
        'SMALLINT': 'IntegerField',
        'REAL': 'FloatField',
        'DOUBLE PRECISION': 'FloatField',
        'NUMERIC': 'FloatField',
        'numeric': 'FloatField',
        'NUMBER': 'FloatField',
        'number': 'FloatField',
        'DATE': 'DateField',
        'TIME': 'TimeField',
        'datetime': 'DateTimeField',
        'Datetime': 'DateTimeField',
        'TIMESTAMP': 'DateTimeField',
        'TIMESTAMPTZ': 'DateTimeField',
    }
    CHOICES_NATIVE_TYPE = (
        ('image', 'A Microsoft binary image'),
        )
    CHOICES_ANSI_TYPE = (
        ('CHAR', 'Fixed=width *n*-character string, padded with spaces as needed'),
        ('VARCHAR', 'Variable-width string with a maximum size of *n* characters'), 
        ('NCHAR', 'Fixed width string supporting an international character set'), 
        ('NVARCHAR', 'Variable-width string supporting an international character set'),
        ('BIT', 'A fixed-length array of *n* bits'),
        ('BIT VARYING', 'An array of up to *n* bits'),
        ('INTEGER', 'An integer'),
        ('SMALLINT', 'A reduced-precision integer'),
        ('FLOAT', 'A floating-point number'),
        ('REAL', 'A floating-point number'),
        ('DOUBLE PRECISION', 'A floating-point number with greater precision'),
        ('NUMERIC', 'A number with arbitratry *precision* and *scale*, e.g. 123.45 has a *precision* of 5 and a *scale* of 2'),
        ('DECIMAL', 'A number with arbitratry *precision* and *scale*, e.g. 123.45 has a *precision* of 5 and a *scale* of 2'),
        ('DATE', 'A date value, e.g. 1970-12-25'),
        ('TIME', 'A time value, typically with precision of 1 "tick" or 100 nanoseconds, e.g. 06:01:02'),
        ('TIMESTAMP', 'A naive date and time value (without timezone information), typically with precision of 1 "tick" or 100 nanoseconds, e.g. 1970-12-25 06:01:02'),
        ('TIMESTAMPTZ', 'A date and time value with timezone, typically with precision of 1 "tick" or 100 nanoseconds, e.g. 1970-12-25 06:01:02'),
        )
    CHOICES_DJANGO_TYPE = (
        (None, 'Null'),
        ('FloatField', 'FloatField'),
        ('ForeignKey', 'ForeignKey'),  # inspectdb produces this
        ('CharField', 'CharField'),  # inspectdb produces this
        ('TextField', 'TextField'),  # inspectdb produces this
        ('IntegerField', 'IntegerField'),
        ('NullBooleanField', 'NullBooleanField'),  # inspectdb produces this
        ('BooleanField', 'BooleanField'),
        ('DecimalField', 'DecimalField'),
        ('DateTimeField', 'DateTimeField'),  # inspectdb produces this
        ('DateField', 'DateField'),
        ('TextField', 'TextField'),  # inspectdb produces this
        ('DecimalField', 'DecimalField'),  # inspectdb produces this
        )
    django_type = models.CharField(choices=CHOICES_DJANGO_TYPE, default=None, max_length=20, null=True)
    ansi_type = models.CharField(choices=CHOICES_ANSI_TYPE, max_length=20, null=True)

    __unicode__ = representation


class Field(models.Model):
    """Metadata about a Database field and its Django Field"""
    _IMPORTANT_FIELDS = ('pk', 'db_column', 'db_table', 'type', 'fraction_distinct')

    # objects = hstore.HStoreManager()

    table_stats = models.ForeignKey(Table)
    django_field = models.CharField(max_length=255, null=False, default='', blank=True) 

    max_length = models.IntegerField(null=True)
    blank = models.BooleanField()
    choices = models.TextField(null=True)

    django_type = models.ForeignKey(Type, null=True, default=None)

    type = models.CharField(max_length=32, null=False, blank=True, default='')
    scale = models.IntegerField(null=True) 
    db_column = models.CharField(max_length=255, null=False, default='', blank=True) 
    display_size = models.IntegerField(null=True) 
    min = models.TextField(help_text='Python string representation (repr) of the minimum value', null=True)   # repr() of minimum value
    max = models.TextField(help_text='Python string representation (repr) of the maximum value', null=True)   # repr() of minimum value
    shortest = models.TextField(help_text='Shortest string among the field values', null=True)
    longest = models.TextField(help_text='Longest string among the field values', null=True)
    num_distinct = models.IntegerField(help_text="count of distinct (different) discrete values within the column",
        null=True, default=None)
    num_null = models.IntegerField(null=True, default=None)
    precision = models.IntegerField(null=True, default=None)
    fraction_distinct = models.FloatField(help_text="num_distinct / float((count - num_null) or 1)",
        null=True, default=None)
    internal_size = models.IntegerField(null=True, default=None) 
    null_ok = models.NullBooleanField(default=None)
    primary_key = models.NullBooleanField(default=None)

    relative = models.ForeignKey('Field', help_text='A modeled foreign key or one-to-one relationship within the django model.', null=True, related_name='relative_source')
    relative_type = models.CharField(choices=(('ForeignKey', 'ForeignKey'), ('OneToOneField', 'OneToOneField'), ('ManyToManyField', 'ManyToManyField')), max_length=20)
    peer = models.ManyToManyField('Field', through='Correlation', help_text='A field statistically related to this one in some way other than as a foreign key')

    # most_frequent = hstore.DictionaryField(db_index=True, default=None, null=True)

    __unicode__ = representation


class Correlation(models.Model):
    "Graph edges (connections) between fields. Can be across tables and databases." 
    source = models.ForeignKey(Field, related_name='source_correlation')
    target = models.ForeignKey(Field, related_name='target_correlation')
    correlation = models.FloatField(null=True)
    mutual_information = models.FloatField(null=True)
    shared_distinct_values = models.IntegerField(help_text='For nonreal, discrete-valued fields (strings, dates), the number of unique values that are shared between the two fields') 
    shared_values = models.IntegerField(help_text='For nonreal, discrete-valued fields (strings, dates), the number of values that are shared between the two fields, including duplicate occurrences of the same value') 
    shared_distinct_words = models.IntegerField(help_text='For strings, the number of unique words that are shared between all the strings in each field=') 
    shared_tokens = models.IntegerField(help_text='For strings, the number of unique tokens (words) that are shared between the two fields, including duplicate occurrences of the same value') 

    __unicode__ = representation


def import_meta(db_meta, db_name, db_date=None, verbosity=1):
    db_obj, db_created = Database.objects.get_or_create(name=db_name, date=datetime.datetime.now())
    for django_model, table_meta in db_meta.iteritems():
        pk = table_meta['Meta'].get('primary_key', None)
        if pk:
            del(table_meta['Meta']['primary_key'])
        table_obj, table_created = Table.objects.get_or_create(database=db_obj, django_model=django_model, **table_meta['Meta'])
        for django_field, field_meta in table_meta.iteritems():
            if django_field == "Meta":
                # The table "Meta" has already been imported when Table object was created
                continue
            if verbosity > 1:
                print django_field
            if 'name' in field_meta and field_meta['name'] == django_field:
                del(field_meta['name'])
            if 'most_frequent' in field_meta:
                field_meta['most_frequent'] = dict((str(k), '%016d' % v) for (k, v) in field_meta['most_frequent'])
                #print field_meta['most_frequent']
                del(field_meta['most_frequent'])  # DatabaseError: can't adapt type 'HStoreDict'       
            field_obj, field_created = Field.objects.get_or_create(table_stats=table_obj, django_field=django_field, **field_meta)
        if pk and pk in table_meta:
            field_obj = Field.objects.get(table_stats=table_obj, django_field=pk, **table_meta[pk])
            table_obj.django_field = field_obj
            table_obj.save()


# def explore_app(app_name='call_center', verbosity=1):
#     db_meta = explore.get_db_meta(app_name, verbosity=verbosity)
#     try:
#         print '&'*100
#         print db_meta
#         print '&'*100
#         return import_meta(db_meta, db_name=app_name)
#     except:
#         return db_meta
