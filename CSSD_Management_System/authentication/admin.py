
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

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
