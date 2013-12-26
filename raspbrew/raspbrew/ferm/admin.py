from django.contrib import admin

# Register your models here.

from .models import FermConfiguration

class FermConfigurationAdmin(admin.ModelAdmin):
    pass
admin.site.register(FermConfiguration, FermConfigurationAdmin)
