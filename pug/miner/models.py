from django.db import models

from pug.nlp import db


class DatabaseCredentials(models.Model):
    database_stats = models.ForeignKey('DatabaseStats')
    ip = models.CharField(max_length=15, null=True)
    uri =  models.CharField(max_length=256, null=True)
    fqdn = models.CharField(max_length=128, null=True)
    user_name = models.CharField(max_length=128, null=True)
    password = models.CharField(max_length=128, null=True)

    def __unicode__(self):
        return db.representation(self)


class DatabaseStats(models.Model):
    database_name = models.CharField(max_length=128, null=False)

    def __unicode__(self):
        return db.representation(self)


class TableStats(models.Model):
    # _important_fields = ('table_name', 'model_name')

    table_name = models.CharField(max_length=256, null=False)
    model_name = models.CharField(max_length=256, null=True)
    primary_key_field = models.ForeignKey('FieldStats')

    def __unicode__(self):
        return db.representation(self)


class FieldStats(models.Model):
    table_stats = models.ForeignKey('TableStats')

    field_type = models.CharField(max_length=64, null=True)  # Django model field type
    # TODO: type = models.ForiegnKey(FieldType)
    #       FieldType should be:
    #            db_type (Oracle, MS, Postgres, SQLite)
    #            column_type_name
    #            column_type_number
    #            field_type  (Django Field)
    column_type_num = models.IntegerField(null=True)
    column_type_name = models.CharField(max_length=64, null=True)
    num_distinct = models.IntegerField()   # count of distinct (different) discrete values within the column
    min = models.TextField()   # minimum value
    max = models.TextField()
    num_null = models.IntegerField()

    def __unicode__(self):
        return db.representation(self)
