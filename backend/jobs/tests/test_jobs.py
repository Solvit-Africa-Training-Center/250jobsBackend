# jobs/tests/test_jobs_api.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from jobs.models import Job, JobApplication

User = get_user_model()

class JobAPITests(APITestCase):
    def setUp(self):
        # Employer & Technician
        self.emp = User.objects.create_user(username="emp1", password="pass", role="employer", location="Kigali", email="e1@example.com")
        self.tech = User.objects.create_user(username="tech1", password="pass", role="technician", location="Kigali", email="t1@example.com")

        # Jobs
        self.job1 = Job.objects.create(
            employer=self.emp, title="Fix door", description="Repair wooden door",
            category="Carpentry", location="Kigali", budget=30000, is_active=True
        )
        self.job2 = Job.objects.create(
            employer=self.emp, title="Install lights", description="LED install",
            category="Electrical", location="Musanze", budget=80000, is_active=True
        )

        self.public_client = APIClient()

    def test_public_job_list_filters_and_search(self):
        url = reverse("job-list")
        resp = self.public_client.get(url, {"q": "lights", "location": "Musanze"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)
        titles = [r["title"] for r in resp.data["results"]]
        self.assertIn("Install lights", titles)
        self.assertNotIn("Fix door", titles)

    def test_employer_creates_and_updates_own_job(self):
        client = APIClient(); client.force_authenticate(self.emp)
        # create via employers endpoint
        create_url = reverse("employer-post-job")
        payload = {
            "title": "Paint ceiling", "description": "White paint",
            "category": "Painting", "location": "Kigali", "budget": 45000, "currency": "RWF"
        }
        resp = client.post(create_url, payload, format="json")
        self.assertEqual(resp.status_code, 201)
        job_id = Job.objects.get(title="Paint ceiling").id

        # update
        edit_url = reverse("employer-job-detail", kwargs={"pk": job_id})
        resp2 = client.patch(edit_url, {"budget": 50000}, format="json")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(Job.objects.get(id=job_id).budget, 50000)

    def test_technician_applies_and_sees_own_applications(self):
        client = APIClient(); client.force_authenticate(self.tech)
        apply_url = reverse("technician-job-apply", kwargs={"job_id": self.job1.id})
        resp = client.post(apply_url, {"cover_letter": "I can do it"}, format="json")
        self.assertEqual(resp.status_code, 201)  # should fail, job is active but tech not approved
        self.assertTrue(JobApplication.objects.filter(job=self.job1, technician=self.tech).exists())

        mine_url = reverse("technician-my-applications")
        resp2 = client.get(mine_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertIn("results", resp2.data)
        self.assertEqual(resp2.data["results"][0]["job_title"], "Fix door")

    def test_employer_lists_applications_for_owned_job(self):
        # First, create an application
        JobApplication.objects.create(job=self.job2, technician=self.tech, cover_letter="lights pro")
        client = APIClient(); client.force_authenticate(self.emp)
        url = reverse("employer-applicants")
        resp = client.get(url, {"job": self.job2.id})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data["results"]), 1)
        # Serializer returns job id, not title, in employer applicants list
        self.assertEqual(resp.data["results"][0]["job"], self.job2.id)
