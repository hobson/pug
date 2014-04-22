from django.db import models

from pug.nlp import db


class NameDescription(models.Model):

class Story(models.Model):
    '''User `Story`: High-Level description of a requirement (feature)--how the user would like to use it

    Contains just enough information for developers to estimate the effort required. 
    Should be less than a few sentences (preferably one) in the everyday or business language of the end user.
    Should captures what the user wants to achieve. 
    It should be fleshed out in a conversation between the users and the team.
    Should be written by or for the customers. This is how they influence development.
    Stories can also be written by developers to express non-functional requirements
    (security, performance, quality, etc.)
    '''
    name = models.CharField(max_length=64, null=True)
    description = models.TextField(null=True)
    # tag = models.ManyToManyField('Tag')
    category = models.CharField(max_length=64, default='', null=False, blank=True)
    author = models.ManyToManyField('User')  # will be available at attribute "authors" (plural)
    task = models.ManyToManyField('Task')

    def __unicode__(self):
        return db.representation(self)


class Task(models.Model):
    '''Development tasks written by developers in technical terms that combine to create a user `Story`
    
    Should include estimated effort (in either developer hours or story points)

    '''
    slug = models.CharField(max_length=16, default='', null=False, blank=True)
    description = models.TextField(null=True)
    name = models.TextField(null=True)
    author = models.ManyToManyField('User')
    developer = models.CharField(max_length=64, null=True)
    tag = models.ManyToManyField('Tag')
    # authors = models.ManyToManyField('User')
    task = models.ManyToManyField('Task')

    def __unicode__(self):
        return db.representation(self)


class Tag(models.Model):
    name

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

