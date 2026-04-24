from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import  SterilizationBatch, InstrumentSet


admin.site.register(SterilizationBatch)
admin.site.register(InstrumentSet)