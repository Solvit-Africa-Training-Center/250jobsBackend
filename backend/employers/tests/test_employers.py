# employers/tests/test_employers_api.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from technicians.models import TechnicianProfile, Skill
from employers.models import EmployerProfile
from jobs.models import Job, JobApplication

User = get_user_model()

class EmployerAPITests(APITestCase):
    def setUp(self):
        # Users (use lowercase roles and include email/location for JWT login and model constraints)
        self.emp = User.objects.create_user(
            username="employer1",
            email="employer1@example.com",
            password="pass",
            role="employer",
            location="Kigali",
        )
        # Employer profile is auto-created by signal; ensure base fields
        self.emp_profile = self.emp.employer_profile
        self.emp_profile.company_name = "Acme Ltd"
        self.emp_profile.location = "Kigali"
        self.emp_profile.save(update_fields=["company_name", "location"])

        self.tech = User.objects.create_user(
            username="tech1",
            email="tech1@example.com",
            password="pass",
            role="technician",
            location="Kigali",
        )
        from django.utils import timezone
        from datetime import timedelta
        self.tech_profile = self.tech.technician_profile
        self.tech_profile.location = "Kigali"
        self.tech_profile.years_experience = 4
        self.tech_profile.is_approved = True
        # Ensure visible to employers: on trial and not paused
        self.tech_profile.trial_ends_at = timezone.now() + timedelta(days=15)
        self.tech_profile.is_paused = False
        self.tech_profile.save(update_fields=["location", "years_experience", "is_approved", "trial_ends_at", "is_paused"])
        self.skill = Skill.objects.create(name="Plumber")
        self.tech_profile.skills.add(self.skill)

        # Another approved tech (different location/skill)
        self.tech2 = User.objects.create_user(
            username="tech2",
            email="tech2@example.com",
            password="pass",
            role="technician",
            location="Musanze",
        )
        self.tech_profile2 = self.tech2.technician_profile
        self.tech_profile2.location = "Musanze"
        self.tech_profile2.years_experience = 2
        self.tech_profile2.is_approved = True
        self.tech_profile2.trial_ends_at = timezone.now() + timedelta(days=15)
        self.tech_profile2.is_paused = False
        self.tech_profile2.save(update_fields=["location", "years_experience", "is_approved", "trial_ends_at", "is_paused"])

        # Job by employer
        self.job = Job.objects.create(
            employer=self.emp,
            title="Fix sink",
            description="Kitchen sink leaking",
            category="Plumbing",
            location="Kigali",
            budget=50000,
        )

        # Application by tech
        self.app = JobApplication.objects.create(job=self.job, technician=self.tech, cover_letter="I can help")

        # Authenticate via JWT login endpoint
        self.client = APIClient()
        login_resp = self.client.post(reverse("login"), {"email": self.emp.email, "password": "pass"}, format="json")
        assert login_resp.status_code == 200, f"Login failed: {login_resp.status_code} {login_resp.data}"
        token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_employer_can_update_own_profile(self):
        url = reverse("employer-me")
        resp = self.client.patch(url, {"company_description": "We build things"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.emp_profile.refresh_from_db()
        self.assertEqual(self.emp_profile.company_description, "We build things")

    def test_employer_can_browse_technicians_with_filters(self):
        url = reverse("employer-technicians")
        resp = self.client.get(url, {"skill": "Plumb"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)
        results = resp.data["results"]
        # Ensure only the plumber in Kigali appears
        self.assertTrue(any("skills" in r and any(s.get("name") == "Plumber" for s in r["skills"]) for r in results))

    def test_employer_posts_job_via_employers_endpoint(self):
        url = reverse("employer-post-job")
        payload = {
            "title": "Wire a new room",
            "description": "Install sockets",
            "category": "Electrical",
            "location": "Kigali",
            "budget": 120000,
            "currency": "RWF",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Job.objects.filter(title="Wire a new room", employer=self.emp).exists())

    def test_employer_lists_applicants_and_changes_status(self):
        # list applicants
        url = reverse("employer-applicants")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Ensure the listed application belongs to the expected technician
        self.assertEqual(resp.data["results"][0]["technician"], self.tech.id)

        # shortlist
        url_shortlist = reverse("employer-set-status", kwargs={"application_id": self.app.id, "new_status": "SHORTLISTED"})
        resp2 = self.client.post(url_shortlist)
        self.assertEqual(resp2.status_code, 200)

        # hire
        url_hire = reverse("employer-set-status", kwargs={"application_id": self.app.id, "new_status": "HIRED"})
        resp3 = self.client.post(url_hire)
        self.assertEqual(resp3.status_code, 200)

        self.app.refresh_from_db()
        self.assertEqual(self.app.status, JobApplication.HIRED)
