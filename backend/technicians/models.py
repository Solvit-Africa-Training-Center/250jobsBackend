from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Avg, Count
from django.utils import timezone


class Skill(models.Model):
    name = models.CharField(max_length=64, unique=True)


class TechnicianProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="technician_profile")
    bio = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    skills = models.ManyToManyField(Skill, blank=True)
    certificates = models.FileField(upload_to="certs/", blank=True, null=True)
    criminal_record = models.FileField(upload_to="criminal_records/", blank=True, null=True)
    criminal_record_uploaded_at = models.DateTimeField(null=True, blank=True)
    criminal_record_expires_at = models.DateTimeField(null=True, blank=True)
    national_id_document = models.FileField(upload_to="identity_docs/", blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    is_approved = models.BooleanField(default=False)  # set by Admin
    is_paused = models.BooleanField(default=False)  # admin can pause if no active subscription
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # 4.75
    rating_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} (Technician)"

    def save(self, *args, **kwargs):
        new_file_pending = bool(getattr(self.criminal_record, "_file", None))
        previous_file_exists = False
        if self.pk and not new_file_pending:
            previous = self.__class__.objects.filter(pk=self.pk).only("criminal_record").first()
            previous_file_exists = bool(previous and previous.criminal_record)
        if self.criminal_record:
            if new_file_pending or not previous_file_exists or not self.criminal_record_uploaded_at:
                now = timezone.now()
                self.criminal_record_uploaded_at = now
                self.criminal_record_expires_at = now + timedelta(days=180)
        else:
            if self.criminal_record_uploaded_at or self.criminal_record_expires_at:
                self.criminal_record_uploaded_at = None
                self.criminal_record_expires_at = None
        super().save(*args, **kwargs)

    @property
    def criminal_record_is_expired(self):
        if not self.criminal_record_expires_at:
            return True
        return timezone.now() >= self.criminal_record_expires_at


class Review(models.Model):
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_left")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["technician"]),
            models.Index(fields=["reviewer"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Rev<{self.technician_id}:{self.reviewer_id}:{self.rating}>"