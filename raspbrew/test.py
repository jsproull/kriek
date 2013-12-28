#!../env-raspbrew/bin/python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,CurrentStatus

probe=Probe(one_wire_Id=':q

#probes=Probe.objects.all()
current=CurrentStatus.create()
current.save()

print current.status





