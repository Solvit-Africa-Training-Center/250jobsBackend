from django.db import models
from django.conf import settings


class Job(models.Model):
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs"
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    category = models.CharField(max_length=64)  # e.g., "Plumbing", "Electrical"
    location = models.CharField(max_length=120, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="RWF")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["location"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        loc = self.location or "N/A"
        return f"{self.title} @ {loc}"


class JobApplication(models.Model):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    HIRED = "HIRED"
    REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (APPLIED, "Applied"),
        (SHORTLISTED, "Shortlisted"),
        (HIRED, "Hired"),
        (REJECTED, "Rejected"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=APPLIED)

    # timestamps for employer workflow
    shortlisted_at = models.DateTimeField(null=True, blank=True)
    hired_at = models.DateTimeField(null=True, blank=True)
    employer_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "technician")
        indexes = [
            models.Index(fields=["job", "status"]),
            models.Index(fields=["technician"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"App<{self.job_id}:{self.technician_id}:{self.status}>"

