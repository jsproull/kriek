from django.db import models

# Create your models here.
# Global (application) settings

class GlobalSettingsManager(models.Manager):
	def get_setting(self, key):
		try:
			setting = GlobalSettings.objects.get(key=key)
		except:
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