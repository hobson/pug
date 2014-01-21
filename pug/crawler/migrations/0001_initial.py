# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WikiItem'
        db.create_table(u'crawler_wikiitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('crawler', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('toc', self.gf('django.db.models.fields.TextField')()),
            ('abstract', self.gf('django.db.models.fields.TextField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('crawled', self.gf('django.db.models.fields.DateTimeField')(unique=True, null=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'crawler', ['WikiItem'])


    def backwards(self, orm):
        # Deleting model 'WikiItem'
        db.delete_table(u'crawler_wikiitem')


    models = {
        u'crawler.wikiitem': {
            'Meta': {'object_name': 'WikiItem'},
            'abstract': ('django.db.models.fields.TextField', [], {}),
            'count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'crawled': ('django.db.models.fields.DateTimeField', [], {'unique': 'True', 'null': 'True'}),
            'crawler': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'toc': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        }
    }

    complete_apps = ['crawler']