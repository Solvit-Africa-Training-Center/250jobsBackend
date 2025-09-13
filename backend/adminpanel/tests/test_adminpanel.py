from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from technicians.models import TechnicianProfile


User = get_user_model()


class AdminPanelTests(APITestCase):
    def setUp(self):
        # Admin user
        self.admin = User.objects.create_user(
            username="administrator",
            email="administrator@example.com",
            password="password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
            location="Kigali",
        )
        # Login as admin to get JWT
        resp = self.client.post(reverse("login"), {"email": self.admin.email, "password": "password123"}, format="json")
        self.assertEqual(resp.status_code, 200)
        token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # A technician not yet approved
        self.tech_user = User.objects.create_user(
            username="tech_admin",
            email="tech_admin@example.com",
            password="password123",
            role="technician",
            location="Huye",
        )
        self.tech_profile = TechnicianProfile.objects.get(user=self.tech_user)
        self.tech_profile.is_approved = False
        self.tech_profile.is_paused = True
        self.tech_profile.save(update_fields=["is_approved", "is_paused"]) 

    def test_pending_list_and_approve(self):
        # Pending list should include the technician
        url_pending = "/api/admin/technicians/pending/"
        resp = self.client.get(url_pending)
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        items = data if isinstance(data, list) else data.get("results", [])
        self.assertTrue(any(item.get("id") == self.tech_profile.id for item in items))

        # Approve action
        url_approve = f"/api/admin/technicians/{self.tech_profile.id}/approve/"
        resp2 = self.client.post(url_approve)
        self.assertEqual(resp2.status_code, 200)

        self.tech_profile.refresh_from_db()
        self.assertTrue(self.tech_profile.is_approved)
        self.assertIsNotNone(self.tech_profile.trial_ends_at)
        self.assertGreater(self.tech_profile.trial_ends_at, timezone.now())
        self.assertFalse(self.tech_profile.is_paused)

    def test_analytics_summary(self):
        # Ensure at least one pending
        self.tech_profile.is_approved = False
        self.tech_profile.save(update_fields=["is_approved"])
        url = "/api/admin/analytics/summary/"  # router base is /api/admin/analytics/
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("pending_approvals", resp.data)
        self.assertGreaterEqual(resp.data["pending_approvals"], 1)
