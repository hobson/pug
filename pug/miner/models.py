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
    name = models.CharField(max_length=128, null=False)
    connection = models.ForeignKey(Connection)

    __unicode__ = db.representation



class Table(models.Model):
    # _important_fields = ('table_name', 'model_name')
    app          = models.CharField(max_length=256, null=True)
    database     = models.ForeignKey(Database)
    name         = models.CharField(max_length=256, null=False)
    django_model = models.CharField(max_length=256, null=True)
    primary_key  = models.OneToOneField('Field')

    __unicode__ = db.representation


class Type(models.Model):
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

    type = models.ForeignKey(Type, null=False)
    max_length = models.IntegerField(null=True)
    null = models.BooleanField()
    blank = models.BooleanField()
    choices = models.TextField(null=True)
    num_distinct = models.IntegerField()   # count of distinct (different) discrete values within the column
    min = models.TextField(help_text='Python string representation (repr) of the minimum value', null=True)   # repr() of minimum value
    max = models.TextField(help_text='Python string representation (repr) of the maximum value', null=True)   # repr() of minimum value
    num_null = models.IntegerField()

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

