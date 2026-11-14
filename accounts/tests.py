from django.test import TestCase
from django.urls import reverse

from .models import User


class SignUpTests(TestCase):
    def signup(self, **overrides):
        data = {
            "first_name": "Hina", "last_name": "Akhtar", "username": "hina", "email": "hina@example.com",
            "role": "organizer", "password1": "Str0ng-pass-123", "password2": "Str0ng-pass-123",
        }
        data.update(overrides)
        return self.client.post(reverse("accounts:signup"), data)

    def test_signup_as_organizer_logs_in_and_goes_to_dashboard(self):
        response = self.signup()
        self.assertRedirects(response, reverse("events:dashboard"))
        self.assertTrue(User.objects.get(username="hina").is_organizer)

    def test_signup_as_attendee(self):
        response = self.signup(role="attendee")
        self.assertRedirects(response, reverse("events:list"))
        self.assertTrue(User.objects.get(username="hina").is_attendee)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user("existing", "hina@example.com", "pass12345!")
        response = self.signup()
        self.assertContains(response, "already exists")

    def test_logout_requires_post(self):
        User.objects.create_user("u", "u@example.com", "pass12345!")
        self.client.login(username="u", password="pass12345!")
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("accounts:logout")), reverse("events:list"))
