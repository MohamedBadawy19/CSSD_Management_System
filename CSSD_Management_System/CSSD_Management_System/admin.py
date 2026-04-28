from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, InstrumentRequest, RequestItem, InventoryItem, SterilizationBatch, InstrumentSet

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'role', 'department', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'department']
    fieldsets = (
        (None,          {'fields': ('email', 'password')}),
        ('Profile',     {'fields': ('role', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2', 'role', 'department')}),
    )

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
admin.site.register(SterilizationBatch)
admin.site.register(InstrumentSet)