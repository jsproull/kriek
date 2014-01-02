#!../env-raspbrew/bin/python
import os,datetime, base64, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,Status,SSR,GlobalSettings,Status

probe=Probe(one_wire_Id='28-00000449e4f6',name='Room',type=5)
probe.save()

probe=Probe(one_wire_Id='28-0000044a00b2',name='Fan',type=4)
probe.save()

probe=Probe(one_wire_Id='28-00000449ef31',name='Wort',type=3)
probe.save()
ssr=SSR(name='Heater SSR', pin=17, heater_or_chiller=1, probe=probe)
ssr.save()
ssr=SSR(name='Chiller SSR', pin=18, heater_or_chiller=1, probe=probe)
ssr.save()


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





