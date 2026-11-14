from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import attendee_required
from events.models import Event

from .models import Booking
from .services import BookingError, book_seats, cancel_booking


@require_POST
@attendee_required
def create_booking(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    try:
        seats = int(request.POST.get("seats", 1))
    except (TypeError, ValueError):
        seats = 0

    try:
        booking = book_seats(event, request.user, seats)
    except BookingError as error:
        messages.error(request, str(error))
        return redirect(event)

    return redirect("bookings:confirmation", reference=booking.reference)


@login_required
def booking_confirmation(request, reference):
    booking = get_object_or_404(
        Booking.objects.select_related("event", "event__category"), reference=reference, attendee=request.user
    )
    return render(request, "bookings/confirmation.html", {"booking": booking})


@attendee_required
def my_bookings(request):
    bookings = request.user.bookings.select_related("event", "event__category")
    now = timezone.now()
    return render(request, "bookings/my_bookings.html", {
        "upcoming": [b for b in bookings if b.is_confirmed and b.event.starts_at >= now],
        "past": [b for b in bookings if b.is_confirmed and b.event.starts_at < now],
        "cancelled": [b for b in bookings if not b.is_confirmed],
    })


@require_POST
@attendee_required
def cancel(request, reference):
    booking = get_object_or_404(Booking, reference=reference, attendee=request.user)
    try:
        cancel_booking(booking, request.user)
    except BookingError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"Booking {booking.reference} has been cancelled and your seats released.")
    return redirect("bookings:my_bookings")
