from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    CustomUser,
    InstrumentRequest,
    RequestItem,
    InventoryItem,
    SterilizationBatch,
    InstrumentSet,
)

admin.site.site_header = "CSSD Management Admin"
admin.site.site_title = "CSSD Admin"
admin.site.index_title = "Operations Console"


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 0
    autocomplete_fields = ["inventory_item"]
    readonly_fields = ["inventory_item", "quantity"]
    can_delete = False

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'role', 'department', 'is_active', 'date_joined']
    list_filter = ['role', 'department', 'is_active', 'is_staff']
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
    list_display = [
        '__str__',
        'requester',
        'department',
        'priority',
        'status',
        'batch_link',
        'last_operator',
        'submitted_at',
        'sterilized_at',
    ]
    list_filter = ['status', 'priority', 'department', 'submitted_at', 'sterilized_at']
    search_fields = ['requester__email', 'department', 'items__inventory_item__name']
    autocomplete_fields = ['requester', 'last_operator', 'batch']
    readonly_fields = [
        'submitted_at',
        'collected_at',
        'cleaned_at',
        'sterilized_at',
        'packed_at',
        'delivered_at',
    ]
    date_hierarchy = 'submitted_at'
    inlines = [RequestItemInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('requester', 'last_operator', 'batch')
            .prefetch_related('items__inventory_item')
        )

    @admin.display(description='Batch')
    def batch_link(self, obj):
        if not obj.batch_id:
            return '-'
        url = reverse('admin:CSSD_Management_System_sterilizationbatch_change', args=[obj.batch_id])
        return format_html('<a href="{}">Batch #{}</a>', url, obj.batch_id)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_stock', 'min_threshold', 'status']
    list_filter = ['category']
    search_fields = ['name', 'category']
    list_editable = ['current_stock', 'min_threshold']
    ordering = ['category', 'name']

@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ['request', 'inventory_item', 'quantity']
    list_filter = ['inventory_item__category']
    search_fields = ['request__id', 'inventory_item__name']
    autocomplete_fields = ['request', 'inventory_item']


@admin.register(SterilizationBatch)
class SterilizationBatchAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'operator',
        'temperature',
        'cycle_duration',
        'status',
        'created_at',
        'daily_report_link',
    ]
    list_filter = ['status', 'operator', 'created_at']
    search_fields = ['operator__email', 'requests__id']
    autocomplete_fields = ['operator']
    date_hierarchy = 'created_at'

    @admin.display(description='Report')
    def daily_report_link(self, obj):
        date_value = obj.created_at.date().isoformat()
        url = f"{reverse('hospital_report')}?date={date_value}"
        return format_html('<a href="{}">Daily report</a>', url)


@admin.register(InstrumentSet)
class InstrumentSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'quantity', 'state', 'updated_at']
    list_filter = ['state', 'type']
    search_fields = ['name', 'type']
