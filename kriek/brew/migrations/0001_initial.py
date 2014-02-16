# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BrewConfiguration'
        db.create_table(u'brew_brewconfiguration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brewconfs', to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('allow_multiple_ssrs', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'brew', ['BrewConfiguration'])

        # Adding M2M table for field probes on 'BrewConfiguration'
        m2m_table_name = db.shorten_name(u'brew_brewconfiguration_probes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brewconfiguration', models.ForeignKey(orm[u'brew.brewconfiguration'], null=False)),
            ('probe', models.ForeignKey(orm[u'common.probe'], null=False))
        ))
        db.create_unique(m2m_table_name, ['brewconfiguration_id', 'probe_id'])

        # Adding M2M table for field ssrs on 'BrewConfiguration'
        m2m_table_name = db.shorten_name(u'brew_brewconfiguration_ssrs')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brewconfiguration', models.ForeignKey(orm[u'brew.brewconfiguration'], null=False)),
            ('ssr', models.ForeignKey(orm[u'common.ssr'], null=False))
        ))
        db.create_unique(m2m_table_name, ['brewconfiguration_id', 'ssr_id'])

        # Adding M2M table for field schedules on 'BrewConfiguration'
        m2m_table_name = db.shorten_name(u'brew_brewconfiguration_schedules')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brewconfiguration', models.ForeignKey(orm[u'brew.brewconfiguration'], null=False)),
            ('schedule', models.ForeignKey(orm[u'common.schedule'], null=False))
        ))
        db.create_unique(m2m_table_name, ['brewconfiguration_id', 'schedule_id'])


    def backwards(self, orm):
        # Deleting model 'BrewConfiguration'
        db.delete_table(u'brew_brewconfiguration')

        # Removing M2M table for field probes on 'BrewConfiguration'
        db.delete_table(db.shorten_name(u'brew_brewconfiguration_probes'))

        # Removing M2M table for field ssrs on 'BrewConfiguration'
        db.delete_table(db.shorten_name(u'brew_brewconfiguration_ssrs'))

        # Removing M2M table for field schedules on 'BrewConfiguration'
        db.delete_table(db.shorten_name(u'brew_brewconfiguration_schedules'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'brew.brewconfiguration': {
            'Meta': {'object_name': 'BrewConfiguration'},
            'allow_multiple_ssrs': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brewconfs'", 'to': u"orm['auth.User']"}),
            'probes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['common.Probe']", 'null': 'True', 'blank': 'True'}),
            'schedules': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['common.Schedule']", 'null': 'True', 'blank': 'True'}),
            'ssrs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['common.SSR']", 'null': 'True', 'blank': 'True'})
        },
        u'common.pid': {
            'Meta': {'object_name': 'PID'},
            'cycle_time': ('django.db.models.fields.FloatField', [], {'default': '2.0'}),
            'd_param': ('django.db.models.fields.FloatField', [], {'default': '4.0'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'i_param': ('django.db.models.fields.FloatField', [], {'default': '80.0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'k_param': ('django.db.models.fields.FloatField', [], {'default': '70.0'}),
            'power': ('django.db.models.fields.IntegerField', [], {'default': '100'})
        },
        u'common.probe': {
            'Meta': {'object_name': 'Probe'},
            'correction_factor': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '6', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_temp_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'one_wire_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'probes'", 'to': u"orm['auth.User']"}),
            'target_temperature': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'temperature': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'common.schedule': {
            'Meta': {'object_name': 'Schedule'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'schedules'", 'to': u"orm['auth.User']"}),
            'probe': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'schedules'", 'null': 'True', 'to': u"orm['common.Probe']"}),
            'scheduleSteps': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['common.ScheduleStep']", 'null': 'True', 'blank': 'True'}),
            'scheduleTimes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['common.ScheduleTime']", 'null': 'True', 'blank': 'True'})
        },
        u'common.schedulestep': {
            'Meta': {'object_name': 'ScheduleStep'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'end_temperature': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'hold_seconds': ('django.db.models.fields.FloatField', [], {'default': '900'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'start_temperature': ('django.db.models.fields.FloatField', [], {}),
            'step_index': ('django.db.models.fields.IntegerField', [], {})
        },
        u'common.scheduletime': {
            'Meta': {'object_name': 'ScheduleTime'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_temperature': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'start_temperature': ('django.db.models.fields.FloatField', [], {}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'common.ssr': {
            'Meta': {'object_name': 'SSR'},
            'degrees_per_minute': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'eta': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'heater_or_chiller': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ssrs'", 'to': u"orm['auth.User']"}),
            'pid': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ssrs'", 'unique': 'True', 'null': 'True', 'to': u"orm['common.PID']"}),
            'pin': ('django.db.models.fields.IntegerField', [], {}),
            'probe': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ssrs'", 'null': 'True', 'to': u"orm['common.Probe']"}),
            'state': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['brew']