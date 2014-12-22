import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _  # get_language_info, 
from django.contrib.auth.models import User, Group, Permission

import decorators as decorate
from nlp import db


@decorate.represent
class NameDescription(models.Model):
    'Mixin with name = CharField(64) and description = TextField()'
    name = models.CharField(max_length=64, default='', null=False, blank=True)
    description = models.TextField(default='', null=False, blank=True)

    class Meta:
        abstract = True


@decorate.represent
class NameDescriptionSlug(NameDescription):
    'Mixin with name = CharField(64) and description = TextField()'
    slug = models.SlugField(verbose_name=_('alias'), unique=True, null=False, blank=True,
                            help_text=_('Abbreviated string uniquely identifying a record. Often called a "slug" and used as URL alias.'))
    class Meta:
        abstract = True


@decorate.represent
class NameDescriptionSlugTag(NameDescription):
    'Mixin with name = CharField(64) and description = TextField()'
    tag = models.ManyToManyField('Tag', help_text=_('Keywords or phrases that categorize or describe a record.'), null=True)

    class Meta:
        abstract = True


@decorate.represent
class Tracked(models.Model):
    '''Track modifications of records in the database (transaction logging at the python level)'''
    pass


@decorate.represent
class Log(models.Model):
    timetag = models.DateTimeField(default=datetime.datetime.now)
    record = models.ForeignKey('Tracked')


@decorate.represent
class State(NameDescriptionSlug):
    iso = models.CharField(help_text=_('2+2-letter codes (e.g. "US-AZ") from ISO standard 3166-2, the US addition to the international province/state codes in ISO 3166-1'), max_length=5, default='', null=False, blank=True)
    usps = models.CharField(help_text=_('Two-letter US Postal Service code for one of the states or territories in the United States'), max_length=2, default='', null=False, blank=True)


@decorate.represent
class Location(models.Model):
    name = models.CharField(max_length=50, default='', null=False, blank=True)
    address = models.CharField(max_length=128, default='', null=False, blank=True)
    postalcode = models.CharField(max_length=9, default='', null=False, blank=True)
    state = models.ForeignKey('State', default=None, null=True, blank=True)


@decorate.represent
class Organization(NameDescriptionSlug):
    abbreviation = models.CharField(max_length=10, default='', blank=True)
    colloquial = models.CharField(max_length=10, default='', blank=True)
    location = models.ManyToManyField('Location', null=True, default=None, blank=True)
    parent = models.ManyToManyField('Organization', null=True, default=None, blank=True)
    user = models.ManyToManyField(User, null=True, default=None, blank=True)
    group = models.ManyToManyField(Group, null=True, default=None, blank=True)


@decorate.represent
class Story(Tracked, NameDescriptionSlugTag):
    '''User `Story`: High-Level description of a requirement (feature)--how the user would like to use it

    Contains just enough information for developers to estimate the effort required. 
    Should be less than a few sentences (preferably one) in the everyday or business language of the end user.
    Should captures what the user wants to achieve. 
    It should be fleshed out in a conversation between the users and the team.
    Should be written by or for the customers. This is how they influence development.
    Stories can also be written by developers to express non-functional requirements
    (security, performance, quality, etc.)
    '''
    # tag = models.ManyToManyField('Tag')
    category = models.CharField(max_length=64, default='', null=False, blank=True)
    author = models.ManyToManyField(User, related_name='story_author')  # will be available at attribute "authors" (plural)
    stakeholder = models.ManyToManyField(User) #, related_name='story_stakeholder') 
    organization = models.ManyToManyField('Organization')
    task = models.ManyToManyField('Task')

    def __unicode__(self):
        return db.representation(self)


@decorate.represent
class Task(Tracked, NameDescriptionSlugTag):
    '''Development tasks written by developers in technical terms that combine to create a user `Story`
    
    Should include estimated effort (in either developer hours or story points)

    '''
    points = models.FloatField(null=True, default=1, blank=True)
    hours = models.FloatField(null=True, default=1, blank=True)
    planned_start = models.DateTimeField(default=None, null=True, blank=True)
    start = models.DateTimeField(default=None, null=True, blank=True)
    finish = models.DateTimeField(default=None, null=True, blank=True)
    author = models.ManyToManyField(User, related_name='task_author')
    developer = models.ManyToManyField(User)  #, related_name='task_developer_user')
    blockers = models.ManyToManyField('Task')

    def __unicode__(self):
        return db.representation(self)


@decorate.represent
class Tag(NameDescriptionSlug):
    pass
