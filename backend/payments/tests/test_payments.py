from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from payments.models import SubscriptionPlan, Payment, Subscription
from unittest.mock import patch
import os


User = get_user_model()


@override_settings(DEBUG=True)
class PaymentsTests(APITestCase):
    def setUp(self):
        # Create a technician user
        self.tech = User.objects.create_user(
            username="tech_pay",
            email="tech_pay@example.com",
            password="password123",
            role="technician",
            location="Kigali",
        )
        # Login as technician to get JWT
        resp = self.client.post(reverse("login"), {"email": self.tech.email, "password": "password123"}, format="json")
        self.assertEqual(resp.status_code, 200)
        token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Ensure a plan exists (post_migrate seeds defaults; avoid unique name conflicts)
        self.plan = SubscriptionPlan.objects.filter(name="Standard 6 Months").first()
        if not self.plan:
            self.plan = SubscriptionPlan.objects.create(name="Standard 6 Months", duration_months=6, price=30000, currency="RWF")

    def test_plans_list(self):
        url = reverse("payments-plans")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(p["name"] == "Standard 6 Months" for p in resp.data))

    def test_subscribe_returns_mock_without_stripe_config(self):
        # Ensure no stripe config is present
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "", "STRIPE_PRICE_6MONTHS": ""}, clear=False):
            url = reverse("payments-subscribe")
            resp = self.client.post(url, {"plan_id": self.plan.id}, format="json")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("checkout_url", resp.data)
            self.assertIn("stripe.mock", resp.data["checkout_url"])

    def test_webhook_completes_payment_and_creates_subscription(self):
        # Create a pending payment tied to a fake session id
        session_id = "cs_test_123"
        Payment.objects.create(
            payer=self.tech,
            amount=self.plan.price,
            currency=self.plan.currency,
            status=Payment.Status.PENDING,
            tx_ref=session_id,
        )

        # Post an unsigned (dev) webhook payload
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": ""}, clear=False):
            url = reverse("payments-webhook-stripe")
            payload = {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": session_id,
                        "invoice": "in_test_001",
                        "subscription": "sub_test_001",
                        "metadata": {"user_id": self.tech.id, "plan_id": self.plan.id},
                    }
                },
            }
            resp = self.client.post(url, payload, format="json")
            self.assertEqual(resp.status_code, 200)

        # Verify payment completed and subscription created
        pmt = Payment.objects.get(tx_ref=session_id)
        self.assertEqual(pmt.status, Payment.Status.COMPLETED)
        self.assertTrue(Subscription.objects.filter(user=self.tech, plan=self.plan, status=Subscription.Status.ACTIVE).exists())

    def test_config_returns_publishable_key(self):
        with patch.dict(os.environ, {"STRIPE_PUBLISHABLE_KEY": "pk_test_abc"}, clear=False):
            url = reverse("payments-config")
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data.get("stripe_publishable_key"), "pk_test_abc")
