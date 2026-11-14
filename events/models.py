from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    icon = models.CharField(
        max_length=40, default="bi-calendar-event", help_text="Bootstrap Icons class, e.g. bi-music-note-beamed"
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class EventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def upcoming(self):
        return self.filter(starts_at__gte=timezone.now())

    def with_seats_booked(self):
        """Annotate each event with the number of seats in confirmed bookings."""
        from bookings.models import Booking

        return self.annotate(
            seats_booked_total=Sum(
                "bookings__seats",
                filter=models.Q(bookings__status=Booking.Status.CONFIRMED),
                default=0,
            )
        )


class Event(models.Model):
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="events")
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, editable=False)
    description = models.TextField()
    starts_at = models.DateTimeField("starts at")
    ends_at = models.DateTimeField("ends at", null=True, blank=True)
    venue = models.CharField(max_length=150)
    city = models.CharField(max_length=80)
    banner = models.ImageField(upload_to="banners/", blank=True)
    total_seats = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Ticket price in PKR. Use 0 for a free event."
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.title)[:150] or "event"
        slug, counter = base, 2
        while Event.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.slug])

    @property
    def is_free(self):
        return self.price == 0

    @property
    def is_past(self):
        return self.starts_at < timezone.now()

    @property
    def seats_booked(self):
        # Use the annotated value when available to avoid an extra query.
        if hasattr(self, "seats_booked_total"):
            return self.seats_booked_total or 0
        from bookings.models import Booking

        return self.bookings.filter(status=Booking.Status.CONFIRMED).aggregate(total=Sum("seats"))["total"] or 0

    @property
    def seats_left(self):
        return max(self.total_seats - self.seats_booked, 0)

    @property
    def is_sold_out(self):
        return self.seats_left == 0

    @property
    def occupancy_percent(self):
        if not self.total_seats:
            return 0
        return round(self.seats_booked * 100 / self.total_seats)
