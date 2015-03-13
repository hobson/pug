from __future__ import print_function
from django.db import models
#import json

from pug.db import db as djdb
from pug.nlp import db, util


def datetime_parser(s, default=None):
    if s:
        return util.clean_wiki_datetime(s)
    return default




class WikiItem(models.Model):
    _important_fields = ('crawler', 'url', 'title', 'modified', 'crawled')
    _item_mapping = { 
         'url': {'name': 'url', 'type': unicode, 'default': '' },
         'title': {'name': 'title', 'type': unicode, 'default': '' },
         'toc': {'name': 'toc', 'type': None, 'default': ''},
         'abstract': {'name': 'abstract', 'type': None, 'default': '' },
         'text': {'name': 'text', 'type': None, 'default': '' },
         'modified': {'name': 'modified', 'type': datetime_parser, 'default': None },
         'crawled': {'name': 'crawled', 'type': datetime_parser, 'default': None  },
         'count': {'name': 'count', 'type': unicode, 'default': None },
         'crawler': {'name': 'crawler', 'type': None, 'default': None },
        }

    crawler = models.CharField(max_length=30, null=True)
    url = models.CharField(max_length=256, unique=True, null=True)
    title = models.CharField(max_length=100, null=True)
    toc = models.TextField(null=True)
    abstract = models.TextField(null=True)
    text = models.TextField(null=True)
    modified = models.DateTimeField(null=True)
    crawled = models.DateTimeField(null=True)
    count = models.TextField(null=True)

    def import_item(self, item, crawler='wiki', truncate_strings=True, verbosity=0):
        """Import a single record from a Scrapy Item dict

        >> WikiItem().import_item({'url': 'http://test.com', 'modified': '13 January 2014 00:15', 'crawler': 'more than thirty characters in this silly name'})  # doctest: +ELLIPSIS
        <WikiItem: WikiItem('more than thirty characters in', u'http://test.com', '', datetime.datetime(2014, 1, 13, 0, 15), '')>
        """
    
        item = dict(item)
        self.crawler = str(crawler)
        for k, v in self._item_mapping.iteritems():
            if verbosity > 2:
                print('%r: %r' % (k, v))
            value = item.get(k, v['default'])
            if value is None:
                continue
            try: 
                value = v['type'](value)
            except:
                pass
            field = self.__class__._meta.get_field_by_name(v['name'])[0]
            if isinstance(value, basestring):
                max_length = getattr(field, 'max_length', None)
                if max_length and len(value) > max_length:
                    if truncate_strings:
                        value = value[:max_length]
                    else:
                        raise RuntimeError('String loaded from json is length %s and destination field max_length is %s.' % (len(value), max_length))
            if isinstance(field, (models.DateTimeField, models.DateField)):
                value = util.clean_wiki_datetime(value)
            setattr(self, v['name'], value)
        return self

    def __unicode__(self):
        return db.representation(self)

def import_wiki_items(item_seq, model=WikiItem,  batch_len=100, db_alias='default', verbosity=2):
    """Import a sequence (queryset, generator, tuple, list) of dicts or django ORM objects into the indicated model"""
    return djdb.import_items(item_seq, dest_model=model, batch_len=batch_len, db_alias=db_alias, verbosity=verbosity)


def import_wiki_json(path='wikipedia_crawler_data.json', model=WikiItem, batch_len=100, db_alias='default', verbosity=2):
    """Read json file and create the appropriate records according to the given database model."""
    return djdb.import_json(path=path, model=model,  batch_len=batch_len, db_alias=db_alias, verbosity=verbosity)

