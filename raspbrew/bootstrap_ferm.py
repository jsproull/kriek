#!../env-raspbrew/bin/python
import os,datetime, base64, json
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,SSR
from raspbrew.status.models import ProbeStatus
from raspbrew.status.models import Status
from raspbrew.globalsettings.models import GlobalSettings

#status=Status(date=timezone.now())
#status.save()
probe,created=Probe.objects.get_or_create(one_wire_Id='28-00000449e4f6',name='Room',type=5)
probe.save()
#status.probes.add(ProbeStatus.cloneFrom(probe))

probe,created=Probe.objects.get_or_create(one_wire_Id='28-0000044a00b2',name='Fan',type=4)
probe.save()
#status.probes.add(ProbeStatus.cloneFrom(probe))

probe,created=Probe.objects.get_or_create(one_wire_Id='28-00000449ef31',name='Wort',type=3)
probe.save()
#status.probes.add(ProbeStatus.cloneFrom(probe))

ssr,created=SSR.objects.get_or_create(name='Heater SSR', pin=17, heater_or_chiller=0, probe=probe)
ssr.save()
ssr,created=SSR.objects.get_or_create(name='Chiller SSR', pin=18, heater_or_chiller=1, probe=probe)
ssr.save()

if created:
	#g=GlobalSettings(key='UNITS', value='metric')
	#g.save()

#print status.toJson(True)


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





