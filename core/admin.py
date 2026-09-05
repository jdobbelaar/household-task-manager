from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "recurrence_type", "last_done", "snooze_until")
    list_filter = ("recurrence_type",)
    search_fields = ("name",)
