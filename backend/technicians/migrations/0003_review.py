from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("technicians", "0002_technicianprofile_created_at_and_more"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField()),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "reviewer",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews_left", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "technician",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="technicians.technicianprofile"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(fields=["technician"], name="technician_idx"),
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(fields=["reviewer"], name="reviewer_idx"),
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(fields=["created_at"], name="created_at_idx"),
        ),
    ]

