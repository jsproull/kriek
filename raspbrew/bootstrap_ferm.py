#!../env-raspbrew/bin/python
import os,datetime, base64, json
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from django.contrib.auth.models import User
from raspbrew.common.models import Probe,SSR
from raspbrew.status.models import ProbeStatus
from raspbrew.status.models import Status
from raspbrew.globalsettings.models import GlobalSettings
from raspbrew.ferm.models import FermConfiguration

from django.utils import timezone
from datetime import datetime, timedelta

user=User.objects.get(pk=1)
fc,created = FermConfiguration.objects.get_or_create(owner=user, name="Ferm Configuration 1")
fc.save()

#status=Status(date=timezone.now())
#status.save()
probe,created=Probe.objects.get_or_create(one_wire_Id='28-00000449e4f6',name='Room',type=4,owner=user)
probe.save()
fc.probes.add(probe)
#status.probes.add(ProbeStatus.cloneFrom(probe))

probe,created=Probe.objects.get_or_create(one_wire_Id='28-0000044a00b2',name='Fan',type=5,owner=user)
probe.save()
fc.probes.add(probe)
#status.probes.add(ProbeStatus.cloneFrom(probe))

probe,created=Probe.objects.get_or_create(one_wire_Id='28-00000449ef31',name='Wort',type=3,owner=user)
probe.save()
fc.probes.add(probe)
#status.probes.add(ProbeStatus.cloneFrom(probe))

ssr,created=SSR.objects.get_or_create(name='Heater SSR', pin=0, heater_or_chiller=0, probe=probe,owner=user)
ssr.save()
fc.ssrs.add(ssr)
ssr,created=SSR.objects.get_or_create(name='Chiller SSR', pin=1, heater_or_chiller=1, probe=probe,owner=user)
ssr.save()
fc.ssrs.add(ssr)

#if created:
	#g=GlobalSettings(key='UNITS', value='metric')
	#g.save()

#print status.toJson(True)


now=timezone.now()
start=now - timedelta(days=7)
d=start
while d < now:
	d=d + timedelta(minutes=5)
	print d
	status,created=Status.objects.get_or_create(date=d, owner=user, fermconfig=fc)
	status.probes.add(ProbeStatus.cloneFrom(probe))
	status.save()
	print status.date

#create some statuseses
#for i in range(0,1000):
#  print i
#  d=datetime.datetime.fromtimestamp(i)
#  status=Status(date=d,status=base64.encodestring(json.dumps({'probes':[], 'dt': d.strftime('%c')}))) 
#  status.save()
  

#probes=Probe.objects.all()
#current=CurrentStatus.create()
#current.save()

#print current.status
