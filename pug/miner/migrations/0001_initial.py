# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Connection'
        db.create_table(u'miner_connection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('uri', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('fqdn', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('port', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'miner', ['Connection'])

        # Adding model 'Database'
        db.create_table(u'miner_database', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=128)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('connection', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['miner.Connection'], null=True)),
        ))
        db.send_create_signal(u'miner', ['Database'])

        # Adding model 'Table'
        db.create_table(u'miner_table', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('app', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('database', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['miner.Database'])),
            ('db_table', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('django_model', self.gf('django.db.models.fields.CharField')(default=None, max_length=256, null=True)),
            ('primary_key', self.gf('django.db.models.fields.related.OneToOneField')(default=None, to=orm['miner.Field'], unique=True, null=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
        ))
        db.send_create_signal(u'miner', ['Table'])

        # Adding model 'ChangeLog'
        db.create_table(u'miner_changelog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('model', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('app', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('primary_key', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('values_hash', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, db_index=True, blank=True)),
        ))
        db.send_create_signal(u'miner', ['ChangeLog'])

        # Adding model 'Type'
        db.create_table(u'miner_type', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('django_type', self.gf('django.db.models.fields.CharField')(default=None, max_length=20, null=True)),
            ('ansi_type', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
        ))
        db.send_create_signal(u'miner', ['Type'])

        # Adding model 'Field'
        db.create_table(u'miner_field', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('table_stats', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['miner.Table'])),
            ('max_length', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('blank', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('choices', self.gf('django.db.models.fields.TextField')(null=True)),
            ('django_type', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['miner.Type'], null=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True)),
            ('scale', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('db_column', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('display_size', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('min', self.gf('django.db.models.fields.TextField')(null=True)),
            ('max', self.gf('django.db.models.fields.TextField')(null=True)),
            ('num_distinct', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('num_null', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('precision', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('fraction_distinct', self.gf('django.db.models.fields.FloatField')(default=None, null=True)),
            ('internal_size', self.gf('django.db.models.fields.IntegerField')(default=None, null=True)),
            ('null_ok', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('primary_key', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('relative', self.gf('django.db.models.fields.related.ForeignKey')(related_name='relative_source', null=True, to=orm['miner.Field'])),
            ('relative_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'miner', ['Field'])

        # Adding model 'Correlation'
        db.create_table(u'miner_correlation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_correlation', to=orm['miner.Field'])),
            ('target', self.gf('django.db.models.fields.related.ForeignKey')(related_name='target_correlation', to=orm['miner.Field'])),
            ('correlation', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('mutual_information', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('shared_distinct_values', self.gf('django.db.models.fields.IntegerField')()),
            ('shared_values', self.gf('django.db.models.fields.IntegerField')()),
            ('shared_distinct_words', self.gf('django.db.models.fields.IntegerField')()),
            ('shared_tokens', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'miner', ['Correlation'])


    def backwards(self, orm):
        # Deleting model 'Connection'
        db.delete_table(u'miner_connection')

        # Deleting model 'Database'
        db.delete_table(u'miner_database')

        # Deleting model 'Table'
        db.delete_table(u'miner_table')

        # Deleting model 'ChangeLog'
        db.delete_table(u'miner_changelog')

        # Deleting model 'Type'
        db.delete_table(u'miner_type')

        # Deleting model 'Field'
        db.delete_table(u'miner_field')

        # Deleting model 'Correlation'
        db.delete_table(u'miner_correlation')


    models = {
        u'miner.changelog': {
            'Meta': {'object_name': 'ChangeLog'},
            'app': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'primary_key': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'values_hash': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        u'miner.connection': {
            'Meta': {'object_name': 'Connection'},
            'fqdn': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'})
        },
        u'miner.correlation': {
            'Meta': {'object_name': 'Correlation'},
            'correlation': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mutual_information': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'shared_distinct_values': ('django.db.models.fields.IntegerField', [], {}),
            'shared_distinct_words': ('django.db.models.fields.IntegerField', [], {}),
            'shared_tokens': ('django.db.models.fields.IntegerField', [], {}),
            'shared_values': ('django.db.models.fields.IntegerField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_correlation'", 'to': u"orm['miner.Field']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'target_correlation'", 'to': u"orm['miner.Field']"})
        },
        u'miner.database': {
            'Meta': {'object_name': 'Database'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['miner.Connection']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128'})
        },
        u'miner.field': {
            'Meta': {'object_name': 'Field'},
            'blank': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'choices': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'db_column': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'display_size': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'django_type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['miner.Type']", 'null': 'True'}),
            'fraction_distinct': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_size': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'max': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'max_length': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'min': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'null_ok': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'num_distinct': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'num_null': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'peer': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['miner.Field']", 'through': u"orm['miner.Correlation']", 'symmetrical': 'False'}),
            'precision': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'primary_key': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'relative': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relative_source'", 'null': 'True', 'to': u"orm['miner.Field']"}),
            'relative_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'scale': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'table_stats': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['miner.Table']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'})
        },
        u'miner.table': {
            'Meta': {'object_name': 'Table'},
            'app': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'database': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['miner.Database']"}),
            'db_table': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'django_model': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '256', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary_key': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': u"orm['miner.Field']", 'unique': 'True', 'null': 'True'})
        },
        u'miner.type': {
            'Meta': {'object_name': 'Type'},
            'ansi_type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'django_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '20', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['miner']