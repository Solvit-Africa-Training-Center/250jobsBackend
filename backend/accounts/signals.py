from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from employers.models import EmployerProfile
from technicians.models import TechnicianProfile


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profiles(sender, instance: User, created: bool, **kwargs):
    if not created:
        return

    role = getattr(instance, "role", "")

    if role == "technician":
        # Create a minimal technician profile if missing
        TechnicianProfile.objects.get_or_create(user=instance)

    elif role == "employer":
        # EmployerProfile requires company_name; use username as a placeholder
        EmployerProfile.objects.get_or_create(
            user=instance,
            defaults={"company_name": instance.username},
        )

