#!../env-raspbrew/bin/python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,CurrentStatus

#probes=Probe.objects.all()
current=CurrentStatus.create()





