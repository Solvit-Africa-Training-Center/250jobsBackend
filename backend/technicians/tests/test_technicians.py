# technicians/tests/test_technicians_api.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from technicians.models import TechnicianProfile, Skill
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class TechnicianAPITests(APITestCase):
    def setUp(self):
        # Skills
        self.skill_plumber = Skill.objects.create(name="Plumber")
        self.skill_electric = Skill.objects.create(name="Electrician")

        # Approved technicians
        self.tech_user1 = User.objects.create_user(username="tech1", password="pass", role="technician", location="Kigali", email="t1@example.com")
        self.tp1 = TechnicianProfile.objects.get(user=self.tech_user1)
        self.tp1.location = "Kigali"
        self.tp1.years_experience = 3
        self.tp1.is_approved = True
        self.tp1.trial_ends_at = timezone.now() + timedelta(days=10)
        self.tp1.is_paused = False
        self.tp1.rating_avg = 4.5
        self.tp1.save(update_fields=["location","years_experience","is_approved","trial_ends_at","is_paused","rating_avg"])
        self.tp1.skills.add(self.skill_plumber)

        self.tech_user2 = User.objects.create_user(username="tech2", password="pass", role="technician", location="Musanze", email="t2@example.com")
        self.tp2 = TechnicianProfile.objects.get(user=self.tech_user2)
        self.tp2.location = "Musanze"
        self.tp2.years_experience = 5
        self.tp2.is_approved = True
        self.tp2.trial_ends_at = timezone.now() + timedelta(days=10)
        self.tp2.is_paused = False
        self.tp2.rating_avg = 4.8
        self.tp2.save(update_fields=["location","years_experience","is_approved","trial_ends_at","is_paused","rating_avg"])
        self.tp2.skills.add(self.skill_electric)

        # Not approved (should be hidden from public list)
        self.tech_user3 = User.objects.create_user(username="tech3", password="pass", role="technician", location="Kigali", email="t3@example.com")
        self.tp3 = TechnicianProfile.objects.get(user=self.tech_user3)
        self.tp3.location = "Kigali"
        self.tp3.years_experience = 2
        self.tp3.is_approved = False
        self.tp3.is_paused = True
        self.tp3.rating_avg = 3.9
        self.tp3.save(update_fields=["location","years_experience","is_approved","is_paused","rating_avg"])
        self.tp3.skills.add(self.skill_plumber)

        # Employer user (for auth checks)
        self.emp_user = User.objects.create_user(username="emp", password="pass", role="employer", location="Kigali", email="emp@example.com")

        self.client = APIClient()

    def test_public_list_technicians_with_filters_and_pagination(self):
        url = reverse("technician-list")
        # Filter by location
        resp = self.client.get(url, {"location": "Kigali"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)
        # Only approved in Kigali -> tp1 (tp3 is not approved)
        results = resp.data["results"]
        # Ensure tp1 appears and tp3 does not (not approved)
        returned_ids = [r.get("id") for r in results]
        self.assertIn(self.tp1.id, returned_ids)
        self.assertNotIn(self.tp3.id, returned_ids)

        # Filter by skill name
        resp2 = self.client.get(url, {"skill": "Electric"})
        self.assertEqual(resp2.status_code, 200)
        ids2 = [r.get("id") for r in resp2.data["results"]]
        self.assertIn(self.tp2.id, ids2)
        self.assertNotIn(self.tp1.id, ids2)

    def test_public_technician_detail(self):
        url = reverse("technician-detail", kwargs={"pk": self.tp1.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Detail no longer exposes username; validate id/location
        self.assertEqual(resp.data["id"], self.tp1.id)
        self.assertEqual(resp.data["location"], "Kigali")

    def test_technician_can_update_own_profile(self):
        self.client.force_authenticate(self.tech_user1)
        url = reverse("technician-me")
        resp = self.client.patch(url, {"bio": "Updated bio", "years_experience": 4}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.tp1.refresh_from_db()
        self.assertEqual(self.tp1.bio, "Updated bio")
        self.assertEqual(self.tp1.years_experience, 4)

    def test_employer_cannot_update_technician_profile_endpoint(self):
        self.client.force_authenticate(self.emp_user)
        url = reverse("technician-me")
        resp = self.client.get(url)
        # Employer has no technician_profile; should 403 or error; our permission is IsTechnician -> 403
        self.assertEqual(resp.status_code, 403)
