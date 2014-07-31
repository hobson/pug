# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Database.date'
        db.add_column(u'miner_database', 'date',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True),
                      keep_default=False)

        # Deleting field 'Field.null'
        db.delete_column(u'miner_field', 'null')

        # Adding field 'Field.scale'
        db.add_column(u'miner_field', 'scale',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

        # Adding field 'Field.db_column'
        db.add_column(u'miner_field', 'db_column',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Field.display_size'
        db.add_column(u'miner_field', 'display_size',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)

        # Adding field 'Field.precision'
        db.add_column(u'miner_field', 'precision',
                      self.gf('django.db.models.fields.IntegerField')(default=None, null=True),
                      keep_default=False)

        # Adding field 'Field.fraction_distinct'
        db.add_column(u'miner_field', 'fraction_distinct',
                      self.gf('django.db.models.fields.FloatField')(default=None, null=True),
                      keep_default=False)

        # Adding field 'Field.internal_size'
        db.add_column(u'miner_field', 'internal_size',
                      self.gf('django.db.models.fields.IntegerField')(default=None, null=True),
                      keep_default=False)

        # Adding field 'Field.null_ok'
        db.add_column(u'miner_field', 'null_ok',
                      self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Field.primary_key'
        db.add_column(u'miner_field', 'primary_key',
                      self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True),
                      keep_default=False)


        # Changing field 'Field.num_distinct'
        db.alter_column(u'miner_field', 'num_distinct', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'Field.num_null'
        db.alter_column(u'miner_field', 'num_null', self.gf('django.db.models.fields.IntegerField')(null=True))
        # Deleting field 'Table.name'
        db.delete_column(u'miner_table', 'name')

        # Adding field 'Table.db_table'
        db.add_column(u'miner_table', 'db_table',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256),
                      keep_default=False)

        # Adding field 'Table.count'
        db.add_column(u'miner_table', 'count',
                      self.gf('django.db.models.fields.IntegerField')(default=None, null=True),
                      keep_default=False)


        # Changing field 'Table.primary_key'
        db.alter_column(u'miner_table', 'primary_key_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['miner.Field'], unique=True, null=True))

    def backwards(self, orm):
        # Deleting field 'Database.date'
        db.delete_column(u'miner_database', 'date')

        # Adding field 'Field.null'
        db.add_column(u'miner_field', 'null',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'Field.scale'
        db.delete_column(u'miner_field', 'scale')

        # Deleting field 'Field.db_column'
        db.delete_column(u'miner_field', 'db_column')

        # Deleting field 'Field.display_size'
        db.delete_column(u'miner_field', 'display_size')

        # Deleting field 'Field.precision'
        db.delete_column(u'miner_field', 'precision')

        # Deleting field 'Field.fraction_distinct'
        db.delete_column(u'miner_field', 'fraction_distinct')

        # Deleting field 'Field.internal_size'
        db.delete_column(u'miner_field', 'internal_size')

        # Deleting field 'Field.null_ok'
        db.delete_column(u'miner_field', 'null_ok')

        # Deleting field 'Field.primary_key'
        db.delete_column(u'miner_field', 'primary_key')


        # Changing field 'Field.num_distinct'
        db.alter_column(u'miner_field', 'num_distinct', self.gf('django.db.models.fields.IntegerField')(default=-1))

        # Changing field 'Field.num_null'
        db.alter_column(u'miner_field', 'num_null', self.gf('django.db.models.fields.IntegerField')(default=-1))
        # Adding field 'Table.name'
        db.add_column(u'miner_table', 'name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256),
                      keep_default=False)

        # Deleting field 'Table.db_table'
        db.delete_column(u'miner_table', 'db_table')

        # Deleting field 'Table.count'
        db.delete_column(u'miner_table', 'count')


        # Changing field 'Table.primary_key'
        db.alter_column(u'miner_table', 'primary_key_id', self.gf('django.db.models.fields.related.OneToOneField')(default='', to=orm['miner.Field'], unique=True))

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
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['miner.Connection']"}),
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
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['miner.Type']"})
        },
        u'miner.table': {
            'Meta': {'object_name': 'Table'},
            'app': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'database': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['miner.Database']"}),
            'db_table': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'django_model': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '256', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary_key': ('django.db.models.fields.related.OneToOneField', [], {'default': 'None', 'to': u"orm['miner.Field']", 'unique': 'True', 'null': 'True'})
        },
        u'miner.type': {
            'Meta': {'object_name': 'Type'},
            'ansi_type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'django_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['miner']