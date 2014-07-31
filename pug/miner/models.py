import datetime

from django.db import models

from pug.nlp import db


class Connection(models.Model):
    "The username, password, IP Address or URL required to access a database"
    ip = models.CharField(max_length=15, null=True)
    uri =  models.CharField(max_length=256, null=True)
    fqdn = models.CharField(max_length=128, null=True)
    user = models.CharField(max_length=128, null=True)
    password = models.CharField(max_length=128, null=True)
    port = models.IntegerField(null=False)

    def __unicode__(self):
        return db.representation(self)


class Database(models.Model):
    """Metadata about a Database (postgres or Microsoft SQL "USE" argument)"""
    name = models.CharField(max_length=128, null=False)
    date = models.DateTimeField(help_text='Timestamp when the metadata was calculated', null=False)
    connection = models.ForeignKey(Connection)

    __unicode__ = db.representation


class Table(models.Model):
    # _important_fields = ('table_name', 'model_name')
    app          = models.CharField(max_length=256, default='', null=False, blank=True)
    database     = models.ForeignKey(Database)
    db_table     = models.CharField(max_length=256, null=False)
    django_model = models.CharField(max_length=256, null=True)
    primary_key  = models.OneToOneField('Field')
    count        = models.IntegerField(null=False)

    __unicode__ = db.representation


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
        'VARCHAR': 'CharField', 
        'NCHAR': 'CharField', 
        'NVARCHAR': 'CharField',
        'SMALLINT': 'IntegerField',
        'REAL': 'FloatField',
        'DOUBLE PRECISION': 'FloatField',
        'NUMERIC': 'DecimalField',
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
    django_type = models.CharField(choices=CHOICES_DJANGO_TYPE, max_length=20, null=False)
    ansi_type = models.CharField(choices=CHOICES_ANSI_TYPE, max_length=20, null=True)

    __unicode__ = db.representation


class Field(models.Model):
    table_stats = models.ForeignKey(Table)

    max_length = models.IntegerField(null=True)
    blank = models.BooleanField()
    choices = models.TextField(null=True)

    type = models.ForeignKey(Type, null=False)
    scale = models.IntegerField(null=True) 
    db_column = models.CharField(max_length=255, null=False, blank=False) 
    display_size = models.IntegerField(null=True) 
    min = models.TextField(help_text='Python string representation (repr) of the minimum value', null=True)   # repr() of minimum value
    max = models.TextField(help_text='Python string representation (repr) of the maximum value', null=True)   # repr() of minimum value
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




    __unicode__ = db.representation


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

    __unicode__ = db.representation




def import_meta(db_meta, db_name, db_date=None):
    db_obj = Database(name=db_name, db_date=datetime.now())
    db_obj.save()
    for table_meta in db_meta:
        table_obj, created = Table(database=db_obj, **table_meta['Meta'])
        table_obj.save()
        for field_name, field_meta in table_meta.iteritems():
            if field_name == "Meta":
                # The table "Meta" has already been imported when Table object was created
                continue  
            field_obj = Field(table=table_obj, **field_meta)
            field_obj.save()