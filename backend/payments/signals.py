from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import SubscriptionPlan, Subscription
from technicians.models import TechnicianProfile
import os


@receiver(post_migrate)
def ensure_default_subscription_plans(sender, **kwargs):
    # Only run after payments app migrations
    app_config = kwargs.get("app_config")
    if not app_config or app_config.label != "payments":
        return

    defaults = [
        {"name": "Standard Monthly", "duration_months": 1, "price": 5000, "currency": "RWF"},
        {"name": "Standard 6 Months", "duration_months": 6, "price": 30000, "currency": "RWF"},
        {"name": "Standard Yearly", "duration_months": 12, "price": 50000, "currency": "RWF"},
    ]
    for d in defaults:
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name=d["name"],
            defaults={
                "duration_months": d["duration_months"],
                "price": d["price"],
                "currency": d["currency"],
            },
        )
        # Optionally attach Stripe price ids from environment variables
        price_env = None
        if d["duration_months"] == 1:
            price_env = os.getenv("STRIPE_PRICE_MONTHLY")
        elif d["duration_months"] == 6:
            price_env = os.getenv("STRIPE_PRICE_6MONTHS")
        elif d["duration_months"] == 12:
            price_env = os.getenv("STRIPE_PRICE_YEARLY")
        if price_env and plan.stripe_price_id != price_env:
            plan.stripe_price_id = price_env
            plan.save(update_fields=["stripe_price_id"])


@receiver(post_save, sender=Subscription)
def ensure_unpaused_on_active_subscription(sender, instance: Subscription, created, **kwargs):
    # If a subscription is created or updated to ACTIVE, unpause technician profile if exists
    try:
        if instance.status == Subscription.Status.ACTIVE:
            tech = TechnicianProfile.objects.get(user=instance.user)
            if tech.is_paused:
                tech.is_paused = False
                tech.save(update_fields=["is_paused"])
    except TechnicianProfile.DoesNotExist:
        pass
