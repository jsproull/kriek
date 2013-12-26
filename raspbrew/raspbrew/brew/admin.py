from django.contrib import admin

# Register your models here.

from .models import BrewConfiguration

class BrewConfigurationAdmin(admin.ModelAdmin):
    pass
admin.site.register(BrewConfiguration, BrewConfigurationAdmin)
