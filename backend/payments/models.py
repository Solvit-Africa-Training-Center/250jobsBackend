from django.db import models
from django.conf import settings
from django.utils import timezone
from jobs.models import Job, JobApplication


class SubscriptionPlan(models.Model):
    MONTHLY = 1
    SIX_MONTH = 6
    YEARLY = 12

    DURATION_CHOICES = (
        (MONTHLY, "Monthly"),
        (SIX_MONTH, "6 Months"),
        (YEARLY, "Yearly"),
    )

    name = models.CharField(max_length=64, unique=True)
    duration_months = models.PositiveIntegerField(choices=DURATION_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RWF")
    stripe_price_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return f"{self.name} ({self.duration_months} mo) - {self.price} {self.currency} "


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        CANCELED = "CANCELED", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["end_date"]),
        ]

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.now()

    def __str__(self):
        return f"Sub<{self.user_id}:{self.plan.name}:{self.status}>"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        REFUNDED = "REFUNDED", "Refunded"
        FAILED = "FAILED", "Failed"

    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments_made"
    )
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments_received", null=True, blank=True
    )
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    application = models.ForeignKey(
        JobApplication, on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RWF")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Provider reconciliation
    tx_ref = models.CharField(max_length=64, blank=True, db_index=True)
    provider_tx_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["payer"]),
            models.Index(fields=["payee"]),
        ]

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    @property
    def payer_full_name(self) -> str:
        if self.payer_id and self.payer:
            full = f"{self.payer.first_name} {self.payer.last_name}".strip()
            return full or self.payer.username
        return ""
    @property
    def payee_full_name(self) -> str:
        if self.payee_id and self.payee:
            full = f"{self.payee.first_name} {self.payee.last_name}".strip()
            return full or self.payee.username
        return ""