from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from technicians.models import TechnicianProfile, Review, Skill
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class ReviewTests(APITestCase):
    def setUp(self):
        self.emp = User.objects.create_user(username="emp1", password="pass", role="employer", location="Kigali", email="e1@example.com")
        self.tech = User.objects.create_user(username="tech1", password="pass", role="technician", location="Kigali", email="t1@example.com")
        self.tp = TechnicianProfile.objects.get(user=self.tech)
        self.tp.location = "Kigali"; self.tp.years_experience = 2; self.tp.is_approved = True
        self.tp.trial_ends_at = timezone.now() + timedelta(days=10)
        self.tp.is_paused = False
        self.tp.save(update_fields=["location","years_experience","is_approved","trial_ends_at","is_paused"])

    def test_create_review_updates_average(self):
        client = APIClient(); client.force_authenticate(self.emp)
        # Employer creates review via employers endpoint
        url = reverse("employer-tech-review", kwargs={"pk": self.tp.id})
        r1 = client.post(url, {"rating": 5, "comment": "Great work"}, format="json")
        self.assertEqual(r1.status_code, 201)
        self.tp.refresh_from_db()
        self.assertEqual(float(self.tp.rating_avg), 5.0)
        self.assertEqual(self.tp.rating_count, 1)

        r2 = client.post(url, {"rating": 3}, format="json")
        self.tp.refresh_from_db()
        self.assertEqual(self.tp.rating_count, 2)
        self.assertAlmostEqual(float(self.tp.rating_avg), 4.0, places=2)

    def test_list_reviews_public(self):
        Review.objects.create(technician=self.tp, reviewer=self.emp, rating=4, comment="Good")
        url = reverse("technician-reviews", kwargs={"pk": self.tp.id})
        public = APIClient()
        resp = public.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]) if isinstance(resp.data, dict) and "results" in resp.data else len(resp.data), 1)
