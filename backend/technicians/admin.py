from django.contrib import admin
from .models import TechnicianProfile


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "location",
        "years_experience",
        "is_approved",
        "is_paused",
        "criminal_record_status",
        "criminal_record_expires_at",
        "trial_ends_at",
        "rating_avg",
        "rating_count",
    )
    list_filter = ("is_approved", "is_paused", "years_experience", "location", "criminal_record_expires_at")
    search_fields = ("user__username", "user__email", "location", "skills__name")
    actions = [
        "approve_selected_profiles",
        "revoke_selected_profiles",
        "pause_selected_profiles",
        "resume_selected_profiles",
    ]

    @admin.display(description="Criminal record")
    def criminal_record_status(self, obj):
        if not obj.criminal_record:
            return "Missing"
        return "Expired" if obj.criminal_record_is_expired else "Valid"

    @admin.action(description="Approve selected technicians")
    def approve_selected_profiles(self, request, queryset):
        from datetime import timedelta
        updated = 0
        for profile in queryset:
            if not profile.trial_ends_at:
                profile.trial_ends_at = profile.created_at + timedelta(days=30)
            profile.is_approved = True
            profile.save(update_fields=["is_approved", "trial_ends_at"])
            updated += 1
        self.message_user(request, f"Approved {updated} technician(s). Trial set when missing.")

    @admin.action(description="Revoke approval for selected technicians")
    def revoke_selected_profiles(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Revoked approval for {updated} technician(s).")

    @admin.action(description="Pause selected technicians")
    def pause_selected_profiles(self, request, queryset):
        updated = queryset.update(is_paused=True)
        self.message_user(request, f"Paused {updated} technician(s).")

    @admin.action(description="Resume selected technicians")
    def resume_selected_profiles(self, request, queryset):
        updated = queryset.update(is_paused=False)
        self.message_user(request, f"Resumed {updated} technician(s).")