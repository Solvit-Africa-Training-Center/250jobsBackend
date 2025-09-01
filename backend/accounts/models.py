from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('technician', 'technician'),
        ('employer', 'employer'),
        ('admin', 'Admin'),
    )

    role = models.CharField(choices=ROLE_CHOICES, max_length=20)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.username}"