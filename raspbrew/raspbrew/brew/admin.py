from django.contrib import admin

# Register your models here.

from .models import Config

class ConfigAdmin(admin.ModelAdmin):
    pass
admin.site.register(Config, ConfigAdmin)
