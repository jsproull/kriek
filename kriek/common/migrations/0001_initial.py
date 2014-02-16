# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ScheduleTime'
        db.create_table(u'common_scheduletime', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('start_temperature', self.gf('django.db.models.fields.FloatField')()),
            ('end_temperature', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'common', ['ScheduleTime'])

        # Adding model 'ScheduleStep'
        db.create_table(u'common_schedulestep', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('step_index', self.gf('django.db.models.fields.IntegerField')()),
            ('start_temperature', self.gf('django.db.models.fields.FloatField')()),
            ('end_temperature', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('active_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('hold_seconds', self.gf('django.db.models.fields.FloatField')(default=900)),
        ))
        db.send_create_signal(u'common', ['ScheduleStep'])

        # Adding model 'Schedule'
        db.create_table(u'common_schedule', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='schedules', to=orm['auth.User'])),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('probe', self.gf('django.db.models.fields.related.ForeignKey')(related_name='schedules', null=True, to=orm['common.Probe'])),
        ))
        db.send_create_signal(u'common', ['Schedule'])

        # Adding M2M table for field scheduleTimes on 'Schedule'
        m2m_table_name = db.shorten_name(u'common_schedule_scheduleTimes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('schedule', models.ForeignKey(orm[u'common.schedule'], null=False)),
            ('scheduletime', models.ForeignKey(orm[u'common.scheduletime'], null=False))
        ))
        db.create_unique(m2m_table_name, ['schedule_id', 'scheduletime_id'])

        # Adding M2M table for field scheduleSteps on 'Schedule'
        m2m_table_name = db.shorten_name(u'common_schedule_scheduleSteps')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('schedule', models.ForeignKey(orm[u'common.schedule'], null=False)),
            ('schedulestep', models.ForeignKey(orm[u'common.schedulestep'], null=False))
        ))
        db.create_unique(m2m_table_name, ['schedule_id', 'schedulestep_id'])

        # Adding model 'Probe'
        db.create_table(u'common_probe', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='probes', to=orm['auth.User'])),
            ('one_wire_id', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('temperature', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
            ('target_temperature', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
            ('correction_factor', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=6, decimal_places=2)),
            ('last_temp_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'common', ['Probe'])

        # Adding model 'PID'
        db.create_table(u'common_pid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cycle_time', self.gf('django.db.models.fields.FloatField')(default=2.0)),
            ('k_param', self.gf('django.db.models.fields.FloatField')(default=70.0)),
            ('i_param', self.gf('django.db.models.fields.FloatField')(default=80.0)),
            ('d_param', self.gf('django.db.models.fields.FloatField')(default=4.0)),
            ('power', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'common', ['PID'])

        # Adding model 'SSR'
        db.create_table(u'common_ssr', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ssrs', to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('pin', self.gf('django.db.models.fields.IntegerField')()),
            ('probe', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ssrs', null=True, to=orm['common.Probe'])),
            ('pid', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ssrs', unique=True, null=True, to=orm['common.PID'])),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('state', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('eta', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('degrees_per_minute', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('heater_or_chiller', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'common', ['SSR'])


    def backwards(self, orm):
        # Deleting model 'ScheduleTime'
        db.delete_table(u'common_scheduletime')

        # Deleting model 'ScheduleStep'
        db.delete_table(u'common_schedulestep')

        # Deleting model 'Schedule'
        db.delete_table(u'common_schedule')

        # Removing M2M table for field scheduleTimes on 'Schedule'
        db.delete_table(db.shorten_name(u'common_schedule_scheduleTimes'))

        # Removing M2M table for field scheduleSteps on 'Schedule'
        db.delete_table(db.shorten_name(u'common_schedule_scheduleSteps'))

        # Deleting model 'Probe'
        db.delete_table(u'common_probe')

        # Deleting model 'PID'
        db.delete_table(u'common_pid')

        # Deleting model 'SSR'
        db.delete_table(u'common_ssr')


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

    complete_apps = ['common']