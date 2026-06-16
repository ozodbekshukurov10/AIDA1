from django.contrib import admin

from .models import AccessKey


@admin.register(AccessKey)
class AccessKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "platform_name", "business_type", "prefix", "is_active", "created_at", "last_used_at")
    search_fields = ("name", "prefix", "platform_name", "business_type", "audience")
    list_filter = ("is_active", "business_type", "created_at")
