from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import InstrumentRequest, RequestItem, InventoryItem



@admin.register(InstrumentRequest)
class InstrumentRequestAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'requester', 'department', 'priority', 'status', 'submitted_at']
    list_filter = ['status', 'priority']
    search_fields = ['requester__email', 'department']

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_stock', 'min_threshold', 'status']
    list_filter = ['category']

admin.site.register(RequestItem)
