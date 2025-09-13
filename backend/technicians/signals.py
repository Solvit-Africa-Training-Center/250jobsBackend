from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count

from .models import Review, TechnicianProfile


def _recompute_rating(technician: TechnicianProfile):
    agg = Review.objects.filter(technician=technician).aggregate(avg=Avg("rating"), cnt=Count("id"))
    avg = agg["avg"] or 0
    cnt = agg["cnt"] or 0
    # Round to 2 decimals to match field
    technician.rating_avg = round(float(avg), 2) if avg else 0
    technician.rating_count = int(cnt)
    technician.save(update_fields=["rating_avg", "rating_count"])


@receiver(post_save, sender=Review)
def review_saved(sender, instance: Review, created, **kwargs):
    _recompute_rating(instance.technician)


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance: Review, **kwargs):
    _recompute_rating(instance.technician)

