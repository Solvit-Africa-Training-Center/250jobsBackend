from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from chat.models import Room, Message

User = get_user_model()


class ChatTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(username="employer", email="employer@example.com", password="password123", role="employer")
        self.technician = User.objects.create_user(username="technician", email="tech@example.com", password="password123", role="technician")
        self.other_user = User.objects.create_user(username="other", email="other@example.com", password="password123", role="technician")

        self.authenticate(self.employer)

    def authenticate(self, user):
        login_url = reverse("login")
        response = self.client.post(
            login_url,
            {"email": user.email, "password": "password123"},
            format="json",
        )
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_room(self):
        url = reverse("send-message")
        data = {"recipient_id": self.technician.id, "content": "Hello!"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("room", response.data)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"]["sender"], self.employer.username)

    def test_list_rooms(self):
        room = Room.objects.create()
        room.participants.add(self.employer, self.technician)

        url = reverse("room-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_send_message(self):
        room = Room.objects.create()
        room.participants.add(self.employer, self.technician)

        url = reverse("send-message")
        data = {"recipient_id": self.technician.id, "content": "Test message"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"]["sender"], self.employer.username)
        self.assertEqual(response.data["message"]["content"], "Test message")

    def test_list_messages(self):
        room = Room.objects.create()
        room.participants.add(self.employer, self.technician)

        Message.objects.create(room=room, sender=self.employer, content="Msg1")
        Message.objects.create(room=room, sender=self.technician, content="Msg2")

        url = reverse("list-messages", kwargs={"room_id": room.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unauthorized_access(self):
        room = Room.objects.create()
        room.participants.add(self.employer, self.technician)

        self.authenticate(self.other_user)

        url = reverse("send-message")
        data = {"recipient_id": self.employer.id, "content": "Hi!"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url = reverse("list-messages", kwargs={"room_id": room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
