#!../env-raspbrew/bin/python
import os,datetime, base64, json
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raspbrew.settings")

from raspbrew.common.models import Probe,SSR
from raspbrew.status.models import ProbeStatus
from raspbrew.status.models import Status
from raspbrew.globalsettings.models import GlobalSettings

# PROBE_TYPE = (
# 	(0, 'Mash'),
# 	(1, 'Boil'),
# 	(2, 'Hot Liquor Tank'),
# 	(3, 'Fermentation Wort'),
# 	(4, 'Fermentation Room'),
# 	(5, 'Fermentation AC Fan'),
# 	(6, 'Other'),

#for ssr in  SSR.objects.all():
#	for brew in ssr.brewconfiguration_set.all():
#		if not brew.allow_multiple_ssrs:
#			for ssr2 in  SSR.objects.all():
#				if ssr2 != ssr: 
#           				print ssr
#

#print Status.objects.all().order_by('date')
status=Status.objects.get(pk=3487)

print status.status
status.save()
print status.status
