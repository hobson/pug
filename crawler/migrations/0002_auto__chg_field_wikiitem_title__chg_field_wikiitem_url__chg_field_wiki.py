# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'WikiItem.title'
        db.alter_column(u'crawler_wikiitem', 'title', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

        # Changing field 'WikiItem.url'
        db.alter_column(u'crawler_wikiitem', 'url', self.gf('django.db.models.fields.CharField')(max_length=256, unique=True, null=True))

        # Changing field 'WikiItem.text'
        db.alter_column(u'crawler_wikiitem', 'text', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'WikiItem.abstract'
        db.alter_column(u'crawler_wikiitem', 'abstract', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'WikiItem.toc'
        db.alter_column(u'crawler_wikiitem', 'toc', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'WikiItem.crawler'
        db.alter_column(u'crawler_wikiitem', 'crawler', self.gf('django.db.models.fields.CharField')(max_length=30, null=True))

    def backwards(self, orm):

        # Changing field 'WikiItem.title'
        db.alter_column(u'crawler_wikiitem', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=100))

        # Changing field 'WikiItem.url'
        db.alter_column(u'crawler_wikiitem', 'url', self.gf('django.db.models.fields.CharField')(default='', max_length=128, unique=True))

        # Changing field 'WikiItem.text'
        db.alter_column(u'crawler_wikiitem', 'text', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'WikiItem.abstract'
        db.alter_column(u'crawler_wikiitem', 'abstract', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'WikiItem.toc'
        db.alter_column(u'crawler_wikiitem', 'toc', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'WikiItem.crawler'
        db.alter_column(u'crawler_wikiitem', 'crawler', self.gf('django.db.models.fields.CharField')(default='wiki', max_length=30))

    models = {
        u'crawler.wikiitem': {
            'Meta': {'object_name': 'WikiItem'},
            'abstract': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'crawled': ('django.db.models.fields.DateTimeField', [], {'unique': 'True', 'null': 'True'}),
            'crawler': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'toc': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '256', 'unique': 'True', 'null': 'True'})
        }
    }

    complete_apps = ['crawler']