from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bookings.services import book_seats

from .models import Category, Event


class EventViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = User.objects.create_user("org", "org@example.com", "pass12345!", role=User.Role.ORGANIZER)
        cls.other_organizer = User.objects.create_user("org2", "org2@example.com", "pass12345!", role=User.Role.ORGANIZER)
        cls.attendee = User.objects.create_user("att", "att@example.com", "pass12345!")
        cls.music = Category.objects.create(name="Music")
        cls.tech = Category.objects.create(name="Technology")

    def make_event(self, **overrides):
        data = {
            "organizer": self.organizer, "category": self.music, "title": "Jazz Night",
            "description": "Live jazz.", "starts_at": timezone.now() + timedelta(days=3),
            "venue": "Arts Council", "city": "Karachi", "total_seats": 10, "price": 0,
        }
        data.update(overrides)
        return Event.objects.create(**data)

    def test_slug_is_unique(self):
        first, second = self.make_event(), self.make_event()
        self.assertEqual(first.slug, "jazz-night")
        self.assertEqual(second.slug, "jazz-night-2")

    def test_listing_hides_past_and_draft_events(self):
        self.make_event(title="Visible")
        self.make_event(title="Old", starts_at=timezone.now() - timedelta(days=1))
        self.make_event(title="Hidden Draft", is_published=False)

        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "Visible")
        self.assertNotContains(response, "Old")
        self.assertNotContains(response, "Hidden Draft")

    def test_search_and_category_filter(self):
        self.make_event(title="Jazz Night")
        self.make_event(title="Python Meetup", category=self.tech, city="Lahore")

        response = self.client.get(reverse("events:list"), {"q": "python"})
        self.assertContains(response, "Python Meetup")
        self.assertNotContains(response, "Jazz Night</a>")

        response = self.client.get(reverse("events:list"), {"category": "music"})
        self.assertContains(response, "Jazz Night")
        self.assertNotContains(response, "Python Meetup")

    def test_draft_detail_is_only_visible_to_organizer(self):
        draft = self.make_event(is_published=False)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

        self.client.force_login(self.organizer)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 200)

    def test_attendee_cannot_access_dashboard_or_create(self):
        self.client.force_login(self.attendee)
        self.assertRedirects(self.client.get(reverse("events:dashboard")), reverse("events:list"))
        self.assertRedirects(self.client.get(reverse("events:create")), reverse("events:list"))

    def test_organizer_can_create_event(self):
        self.client.force_login(self.organizer)
        starts_at = (timezone.localtime() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("events:create"), {
            "title": "New Workshop", "category": self.tech.pk, "description": "Hands-on.",
            "starts_at": starts_at, "venue": "Colabs", "city": "Lahore",
            "total_seats": 30, "price": "1500", "is_published": "on",
        })
        event = Event.objects.get(title="New Workshop")
        self.assertRedirects(response, event.get_absolute_url())
        self.assertEqual(event.organizer, self.organizer)

    def test_organizer_cannot_edit_others_events(self):
        event = self.make_event()
        self.client.force_login(self.other_organizer)
        self.assertEqual(self.client.get(reverse("events:update", args=[event.slug])).status_code, 404)
        self.assertEqual(self.client.post(reverse("events:delete", args=[event.slug])).status_code, 404)
        self.assertTrue(Event.objects.filter(pk=event.pk).exists())

    def test_capacity_cannot_drop_below_booked_seats(self):
        event = self.make_event()
        book_seats(event, self.attendee, 6)
        self.client.force_login(self.organizer)

        response = self.client.post(reverse("events:update", args=[event.slug]), {
            "title": event.title, "category": self.music.pk, "description": event.description,
            "starts_at": timezone.localtime(event.starts_at).strftime("%Y-%m-%dT%H:%M"),
            "venue": event.venue, "city": event.city, "total_seats": 4, "price": "0", "is_published": "on",
        })
        self.assertContains(response, "capacity cannot be lower")
        event.refresh_from_db()
        self.assertEqual(event.total_seats, 10)

    def test_dashboard_shows_seats_left(self):
        event = self.make_event()
        book_seats(event, self.attendee, 3)
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("events:dashboard"))
        self.assertContains(response, "3 / 10")
        self.assertContains(response, "7 left")
