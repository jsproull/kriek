from __future__ import absolute_import

from celery import shared_task
from kriek.globalsettings.models import GlobalSettings
from kriek.common.models import Status
import time

@shared_task
def purgeAllData():

	#turn off updates
	g, created = GlobalSettings.objects.get_or_create(key='UPDATES_ENABLED')
	g.value = False
	g.save()

	#delete all objects
	Status.objects.all().delete();

	#turn updates back on
	g.value = True
	g.save()
