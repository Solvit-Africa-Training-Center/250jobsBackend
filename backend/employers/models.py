from django.db import models
from django.conf import settings

class EmployerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employer_profile")
    company_name = models.CharField(max_length=120)
    company_description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.company_name or self.user.username

