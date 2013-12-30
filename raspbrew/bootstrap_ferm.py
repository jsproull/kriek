#!../env-raspbrew/bin/python
import os,datetime, base64, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,Status,SSR,GlobalSettings,Status

probe=Probe(one_wire_Id='28-00000449e4f6',name='Room',type=4)
probe.save()

probe=Probe(one_wire_Id='28-0000044a00b2',name='Wort',type=3)
probe.save()
ssr=SSR(name='Boil SSR', pin=23, heater_or_chiller=0, probe=probe)
ssr.save()
ssr=SSR(name='HLT SSR', pin=22, heater_or_chiller=1, probe=probe)
ssr.save()

probe=Probe(one_wire_Id='28-00000449ef31',name='Fan',type=5)
probe.save()

g=GlobalSettings(key='UNITS', value='metric')
g.save()

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





