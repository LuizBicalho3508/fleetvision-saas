from django.contrib import admin
from .models import Tenant, UserProfile

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'is_active', 'created_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'tenant', 'phone')
    list_filter = ('role', 'tenant')
    search_fields = ('user__username', 'user__email', 'tenant__name')