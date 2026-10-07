
from django.contrib import admin
from django.utils import timezone

from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "approved", "approved_at")
    list_filter = ("approved", "role")
    search_fields = ("user__username", "user__email")

    def save_model(self, request, obj, form, change):
        if obj.approved and not obj.approved_at:
            obj.approved_at = timezone.now()

        if not obj.approved:
            obj.approved_at = None

        super().save_model(request, obj, form, change)

