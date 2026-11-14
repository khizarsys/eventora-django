"""Booking business logic, kept out of views so it can be tested directly."""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from events.models import Event

from .models import Booking


class BookingError(Exception):
    """Raised when a booking or cancellation is not allowed."""


@transaction.atomic
def book_seats(event, attendee, seats):
    """
    Reserve `seats` for `attendee` and return the new Booking.

    The event row is locked with SELECT ... FOR UPDATE so two concurrent
    requests cannot both pass the availability check and overbook the event
    (on PostgreSQL; SQLite serialises writes anyway).
    """
    event = Event.objects.select_for_update().get(pk=event.pk)

    if not attendee.is_attendee:
        raise BookingError("Only attendee accounts can book seats.")
    if not event.is_published:
        raise BookingError("This event is not open for booking.")
    if event.is_past:
        raise BookingError("This event has already started.")
    if seats < 1:
        raise BookingError("Please book at least one seat.")
    if seats > Booking.MAX_SEATS_PER_BOOKING:
        raise BookingError(f"You can book at most {Booking.MAX_SEATS_PER_BOOKING} seats at a time.")

    seats_left = event.seats_left
    if seats_left == 0:
        raise BookingError("Sorry, this event is sold out.")
    if seats > seats_left:
        raise BookingError(f"Only {seats_left} seat{'s' if seats_left != 1 else ''} left for this event.")

    booking = Booking.objects.create(event=event, attendee=attendee, seats=seats, unit_price=event.price)
    transaction.on_commit(lambda: send_confirmation_email(booking))
    return booking


@transaction.atomic
def cancel_booking(booking, user):
    """Cancel a confirmed booking owned by `user`, freeing its seats."""
    booking = Booking.objects.select_for_update().select_related("event").get(pk=booking.pk)

    if booking.attendee_id != user.pk:
        raise BookingError("You can only cancel your own bookings.")
    if not booking.is_confirmed:
        raise BookingError("This booking is already cancelled.")
    if booking.event.is_past:
        raise BookingError("Bookings cannot be cancelled after the event has started.")

    booking.status = Booking.Status.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=["status", "cancelled_at"])
    return booking


def send_confirmation_email(booking):
    """Send a plain-text confirmation (printed to the console in development)."""
    context = {"booking": booking, "event": booking.event, "user": booking.attendee}
    send_mail(
        subject=f"Booking confirmed: {booking.event.title} ({booking.reference})",
        message=render_to_string("emails/booking_confirmation.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.attendee.email],
        fail_silently=True,
    )
