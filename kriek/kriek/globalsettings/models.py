from django.db import models

# Create your models here.
# Global (application) settings


class GlobalSettingsManager(models.Manager):
	def get_setting(self, key):
		try:
			setting = GlobalSettings.objects.get(key=key)
		except:
			#defaults
			if key == 'UNITS':
				g, created = GlobalSettings.objects.get_or_create(key='UNITS', value='metric')
				g.save()
				setting = GlobalSettings.objects.get(key=key)
			if key == 'UPDATES_ENABLED':
				g, created = GlobalSettings.objects.get_or_create(key='UPDATES_ENABLED', value='True')
				g.save()
				setting = GlobalSettings.objects.get(key=key)
			else:
				raise Exception
		return setting


class GlobalSettings(models.Model):
	key = models.CharField(unique=True, max_length=255)
	value = models.CharField(max_length=255)

	objects = GlobalSettingsManager()

	def __unicode__(self):
		return self.key + " : " + self.value

	class Meta:
		verbose_name = "Global Setting"
		verbose_name_plural = "Global Settings"