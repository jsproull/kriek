from django.test import TestCase

# Create your tests here.
from kriek.globalsettings.models import GlobalSettings

class GlobalSettingsTestCase(TestCase):
	def setUp(self):
		GlobalSettings.objects.create(key='UNITS', value='metric')

	def test_defaults(self):
		units = GlobalSettings.objects.get_setting('UNITS').value
		self.assertEqual(units, 'metric')