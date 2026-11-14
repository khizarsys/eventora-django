import secrets

from django.conf import settings
from django.db import models


def generate_reference():
    """Short, human-friendly booking reference such as EVT-7K2Q9M."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "EVT-" + "".join(secrets.choice(alphabet) for _ in range(6))


class Booking(models.Model):
    MAX_SEATS_PER_BOOKING = 10

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="bookings")
    attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    seats = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    reference = models.CharField(max_length=12, unique=True, default=generate_reference, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} · {self.event} ({self.seats} seat{'s' if self.seats != 1 else ''})"

    @property
    def total_price(self):
        return self.unit_price * self.seats

    @property
    def is_confirmed(self):
        return self.status == self.Status.CONFIRMED

    @property
    def can_cancel(self):
        return self.is_confirmed and not self.event.is_past
