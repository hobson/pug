from __future__ import print_function
from django.db import models
import json

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


def import_items(item_seq, model=WikiItem,  batch_size=100, db_alias='default', verbosity=2):
    """Given a sequence (generator, tuple, list) of dicts import them into the given model"""

    num_items = len(item_seq)
    if verbosity > 1:
        print('Loading %r records from sequence provided...' % len(item_seq))
    for batch_num, dict_batch in enumerate(util.generate_batches(item_seq, batch_size)):
        if verbosity > 2:
            print(repr(dict_batch))
            print(repr((batch_num, len(dict_batch), batch_size)))
            print(type(dict_batch))
        item_batch = []
        for d in dict_batch:
            if verbosity > 2:
                print(repr(d))
            m = model()
            m.import_item(d, verbosity=verbosity)
            item_batch += [m]
        if verbosity > 1:
            print('Writing {0} {1} items in batch {2} out of {3} batches to the {3} database...'.format(
                len(item_batch), model.__name__, batch_num, int(num_items / float(batch_size)), db_alias))
        model.objects.bulk_create(item_batch)


def import_json(path='wikipedia_crawler_data.json', model=WikiItem, batch_size=100, db_alias='default',
    verbosity=2):
    """Read json file and create the appropriate records according to the given database model."""

    # TODO: use a generator to save memory for large json files/databases
    if verbosity:
        print('Reading json records (dictionaries) from {0}.'.format(repr(path)))
    item_list = json.load(open(path, 'r'))
    if verbosity:
        print('Finished reading {0} items from {1}.'.format(len(item_list), repr(path)))
    import_items(item_list, model=model, batch_size=batch_size, db_alias=db_alias, verbosity=verbosity)

