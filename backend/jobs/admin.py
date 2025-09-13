from django.contrib import admin
from .models import Job, JobApplication


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "category", "location", "is_active", "created_at")
    list_filter = ("is_active", "category", "location", "created_at")
    search_fields = ("title", "description", "employer__username", "location")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "technician", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "technician__username")
    actions = ["mark_as_hired", "mark_as_rejected"]

    @admin.action(description="Mark selected as HIRED")
    def mark_as_hired(self, request, queryset):
        updated = queryset.update(status=JobApplication.HIRED)
        self.message_user(request, f"Marked {updated} application(s) as HIRED.")

    @admin.action(description="Mark selected as REJECTED")
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status=JobApplication.REJECTED)
        self.message_user(request, f"Marked {updated} application(s) as REJECTED.")
