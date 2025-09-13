from django.db import models
from django.conf import settings
from django.db.models import Avg, Count

class Skill(models.Model):
    name = models.CharField(max_length=64, unique=True)

class TechnicianProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="technician_profile")
    bio = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    skills = models.ManyToManyField(Skill, blank=True)
    certificates = models.FileField(upload_to="certs/", blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    is_approved = models.BooleanField(default=False)  # set by Admin
    is_paused = models.BooleanField(default=False)  # admin can pause if no active subscription
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # 4.75
    rating_count = models.PositiveIntegerField(default=0)

    def __str__(self): return f"{self.user.username} (Technician)"


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
