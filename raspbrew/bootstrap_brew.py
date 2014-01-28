#!../env-raspbrew/bin/python
import os,datetime, base64, json
from datetime import timedelta
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from django.contrib.auth.models import User
from raspbrew.common.models import Probe,SSR,Schedule,ScheduleTime
from raspbrew.status.models import ProbeStatus
from raspbrew.status.models import Status
from raspbrew.globalsettings.models import GlobalSettings
from raspbrew.brew.models import BrewConfiguration

user=User.objects.get(pk=1)
print user
# PROBE_TYPE = (
# 	(0, 'Mash'),
# 	(1, 'Boil'),
# 	(2, 'Hot Liquor Tank'),
# 	(3, 'Fermentation Wort'),
# 	(4, 'Fermentation Room'),
# 	(5, 'Fermentation AC Fan'),
# 	(6, 'Other'),
bc,created = BrewConfiguration.objects.get_or_create(owner=user, name="Brew Configuration 1")
bc.save()
#bc1,created = BrewConfiguration.objects.get_or_create(owner=user, name="Brew Configuration 2")
#bc1.save()

#HLT
probeh,created=Probe.objects.get_or_create(one_wire_Id='28-00000284da09',name='HLT',type=2,owner=user)
probeh.save()
bc.probes.add(probeh)
ssr,created=SSR.objects.get_or_create(name='HLT SSR', pin=4, heater_or_chiller=0, probe=probeh,owner=user)
ssr.save()
bc.ssrs.add(ssr)

#Boil
probe,created=Probe.objects.get_or_create(one_wire_Id='28-00000284b7a6',name='Boil',type=1,owner=user)
probe.save()
bc.probes.add(probe)
ssr,created=SSR.objects.get_or_create(name='Boil SSR', pin=5, heater_or_chiller=0, probe=probe,owner=user)
ssr.save()
bc.ssrs.add(ssr)

#Mash
probe,created=Probe.objects.get_or_create(one_wire_Id='28-00000284cc3f',name='Mash',type=0,owner=user)
probe.save()
bc.probes.add(probe)

#Chiller
probe,created=Probe.objects.get_or_create(one_wire_Id='28-0000044a0052',name='Boil Chiller',type=6,owner=user)
probe.save()
bc.probes.add(probe)
ssr,created=SSR.objects.get_or_create(name='Boil Chiller SSR', pin=3, heater_or_chiller=0, probe=probe,owner=user)
ssr.save()
bc.ssrs.add(ssr)

#schedules
s,created=Schedule.objects.get_or_create(name="Stepping", owner=user, probe=probeh)
bc.schedules.add(s)

t=timezone.now()
for r in range(1000):
	s1,created=ScheduleTime.objects.get_or_create(start_time=t+timedelta(seconds=r*10), hold_until_time=t+timedelta(seconds=(r+1)*10), target_temperature=float(r)/4)
	print s1.target_temperature
	s.scheduleTime.add(s1)
	s.save()


g,created=GlobalSettings.objects.get_or_create(key='UNITS', value='metric')
g.save()

#if created:
#	g=GlobalSettings(key='UNITS', value='metric')
#	g.save()

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





