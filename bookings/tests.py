from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from events.models import Category, Event

from .models import Booking
from .services import BookingError, book_seats, cancel_booking


class BookingTestMixin:
    """Shared fixtures: one organizer, two attendees and a 5-seat event."""

    @classmethod
    def setUpTestData(cls):
        cls.organizer = User.objects.create_user(
            "organizer", "organizer@example.com", "pass12345!", role=User.Role.ORGANIZER
        )
        cls.attendee = User.objects.create_user("attendee", "attendee@example.com", "pass12345!", first_name="Sara")
        cls.other_attendee = User.objects.create_user("other", "other@example.com", "pass12345!")
        cls.category = Category.objects.create(name="Music")

    def setUp(self):
        self.event = self.make_event()

    def make_event(self, **overrides):
        data = {
            "organizer": self.organizer,
            "category": self.category,
            "title": "Test Concert",
            "description": "A test event.",
            "starts_at": timezone.now() + timedelta(days=7),
            "venue": "Test Hall",
            "city": "Lahore",
            "total_seats": 5,
            "price": 1000,
        }
        data.update(overrides)
        return Event.objects.create(**data)


class BookSeatsServiceTests(BookingTestMixin, TestCase):
    def test_booking_reduces_seats_left(self):
        booking = book_seats(self.event, self.attendee, 3)

        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(self.event.seats_left, 2)
        self.assertTrue(booking.reference.startswith("EVT-"))

    def test_booking_stores_price_at_time_of_booking(self):
        booking = book_seats(self.event, self.attendee, 2)
        self.event.price = 5000
        self.event.save()

        booking.refresh_from_db()
        self.assertEqual(booking.total_price, 2000)

    def test_cannot_book_more_seats_than_available(self):
        book_seats(self.event, self.attendee, 4)

        with self.assertRaisesMessage(BookingError, "Only 1 seat left"):
            book_seats(self.event, self.other_attendee, 2)
        self.assertEqual(self.event.seats_booked, 4)

    def test_cannot_book_sold_out_event(self):
        book_seats(self.event, self.attendee, 5)

        with self.assertRaisesMessage(BookingError, "sold out"):
            book_seats(self.event, self.other_attendee, 1)

    def test_exact_remaining_seats_can_be_booked(self):
        book_seats(self.event, self.attendee, 3)
        book_seats(self.event, self.other_attendee, 2)

        self.assertTrue(self.event.is_sold_out)

    def test_cancelled_bookings_do_not_count_towards_capacity(self):
        booking = book_seats(self.event, self.attendee, 5)
        cancel_booking(booking, self.attendee)

        book_seats(self.event, self.other_attendee, 5)
        self.assertEqual(self.event.seats_left, 0)

    def test_seat_count_must_be_positive(self):
        with self.assertRaises(BookingError):
            book_seats(self.event, self.attendee, 0)

    def test_seat_count_has_per_booking_limit(self):
        big_event = self.make_event(title="Big Event", total_seats=100)
        with self.assertRaisesMessage(BookingError, "at most"):
            book_seats(big_event, self.attendee, Booking.MAX_SEATS_PER_BOOKING + 1)

    def test_cannot_book_past_event(self):
        past = self.make_event(title="Past Event", starts_at=timezone.now() - timedelta(days=1))
        with self.assertRaisesMessage(BookingError, "already started"):
            book_seats(past, self.attendee, 1)

    def test_cannot_book_unpublished_event(self):
        draft = self.make_event(title="Draft Event", is_published=False)
        with self.assertRaisesMessage(BookingError, "not open"):
            book_seats(draft, self.attendee, 1)

    def test_organizer_cannot_book(self):
        with self.assertRaisesMessage(BookingError, "Only attendee"):
            book_seats(self.event, self.organizer, 1)

    def test_confirmation_email_is_sent(self):
        with self.captureOnCommitCallbacks(execute=True):
            booking = book_seats(self.event, self.attendee, 2)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(booking.reference, mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["attendee@example.com"])
        self.assertIn("Test Hall", mail.outbox[0].body)


class CancelBookingServiceTests(BookingTestMixin, TestCase):
    def test_cancel_releases_seats(self):
        booking = book_seats(self.event, self.attendee, 3)
        cancel_booking(booking, self.attendee)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(self.event.seats_left, 5)

    def test_cannot_cancel_someone_elses_booking(self):
        booking = book_seats(self.event, self.attendee, 1)
        with self.assertRaisesMessage(BookingError, "your own"):
            cancel_booking(booking, self.other_attendee)

    def test_cannot_cancel_twice(self):
        booking = book_seats(self.event, self.attendee, 1)
        cancel_booking(booking, self.attendee)
        with self.assertRaisesMessage(BookingError, "already cancelled"):
            cancel_booking(booking, self.attendee)

    def test_cannot_cancel_after_event_started(self):
        booking = book_seats(self.event, self.attendee, 1)
        Event.objects.filter(pk=self.event.pk).update(starts_at=timezone.now() - timedelta(hours=1))
        with self.assertRaisesMessage(BookingError, "after the event has started"):
            cancel_booking(booking, self.attendee)


class BookingViewTests(BookingTestMixin, TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(reverse("bookings:create", args=[self.event.slug]), {"seats": 1})
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('bookings:create', args=[self.event.slug])}")
        self.assertFalse(Booking.objects.exists())

    def test_attendee_books_and_sees_confirmation(self):
        self.client.force_login(self.attendee)
        response = self.client.post(reverse("bookings:create", args=[self.event.slug]), {"seats": 2}, follow=True)

        booking = Booking.objects.get()
        self.assertRedirects(response, reverse("bookings:confirmation", args=[booking.reference]))
        self.assertContains(response, booking.reference)
        self.assertContains(response, "re going!")

    def test_overbooking_shows_error_and_creates_nothing(self):
        self.client.force_login(self.attendee)
        response = self.client.post(reverse("bookings:create", args=[self.event.slug]), {"seats": 6}, follow=True)

        self.assertContains(response, "Only 5 seats left")
        self.assertFalse(Booking.objects.exists())

    def test_invalid_seat_value_is_rejected(self):
        self.client.force_login(self.attendee)
        self.client.post(reverse("bookings:create", args=[self.event.slug]), {"seats": "abc"})
        self.assertFalse(Booking.objects.exists())

    def test_my_bookings_lists_only_own_bookings(self):
        own = book_seats(self.event, self.attendee, 1)
        other = book_seats(self.event, self.other_attendee, 1)
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("bookings:my_bookings"))
        self.assertContains(response, own.reference)
        self.assertNotContains(response, other.reference)

    def test_cannot_view_someone_elses_confirmation(self):
        booking = book_seats(self.event, self.other_attendee, 1)
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("bookings:confirmation", args=[booking.reference]))
        self.assertEqual(response.status_code, 404)

    def test_cancel_view(self):
        booking = book_seats(self.event, self.attendee, 2)
        self.client.force_login(self.attendee)

        response = self.client.post(reverse("bookings:cancel", args=[booking.reference]))
        self.assertRedirects(response, reverse("bookings:my_bookings"))
        booking.refresh_from_db()
        self.assertFalse(booking.is_confirmed)

    def test_cancel_requires_post(self):
        booking = book_seats(self.event, self.attendee, 2)
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("bookings:cancel", args=[booking.reference]))
        self.assertEqual(response.status_code, 405)
