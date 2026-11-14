from datetime import timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import organizer_required
from bookings.models import Booking

from .forms import EventFilterForm, EventForm
from .models import Category, Event


def event_list(request):
    """Public listing of upcoming published events with search and filters."""
    events = Event.objects.published().upcoming().select_related("category", "organizer").with_seats_booked()
    form = EventFilterForm(request.GET or None)

    if form.is_valid():
        data = form.cleaned_data
        if data["q"]:
            q = data["q"]
            events = events.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(venue__icontains=q) | Q(city__icontains=q)
            )
        if data["category"]:
            events = events.filter(category=data["category"])
        if data["date"]:
            events = events.filter(starts_at__date=data["date"])
        elif data["when"]:
            today = timezone.localdate()
            days = {"today": 0, "week": 7, "month": 30}[data["when"]]
            events = events.filter(starts_at__date__lte=today + timedelta(days=days))
        if data["price"] == "free":
            events = events.filter(price=0)
        elif data["price"] == "paid":
            events = events.filter(price__gt=0)

    page = Paginator(events.order_by("starts_at", "pk"), 9).get_page(request.GET.get("page"))
    # Keep the active filters in pagination links.
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "events/event_list.html", {
        "page_obj": page,
        "form": form,
        "categories": Category.objects.all(),
        "active_category": request.GET.get("category", ""),
        "querystring": params.urlencode(),
        "is_filtered": any(value for key, value in request.GET.items() if key != "page"),
    })


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related("category", "organizer"), slug=slug)

    # Unpublished events are only visible to their organizer.
    if not event.is_published and event.organizer != request.user:
        raise Http404("Event not found")

    user_bookings = []
    if request.user.is_authenticated:
        user_bookings = event.bookings.filter(attendee=request.user, status=Booking.Status.CONFIRMED)

    related = (
        Event.objects.published().upcoming().filter(category=event.category)
        .exclude(pk=event.pk).select_related("category").with_seats_booked()[:3]
    )
    return render(request, "events/event_detail.html", {
        "event": event,
        "user_bookings": user_bookings,
        "related_events": related,
        "seat_options": range(1, min(Booking.MAX_SEATS_PER_BOOKING, event.seats_left) + 1),
    })


@organizer_required
def dashboard(request):
    """Organizer overview: their events, bookings per event and seats left."""
    events = (
        request.user.events.select_related("category").with_seats_booked()
        .annotate(booking_count=Count("bookings", filter=Q(bookings__status=Booking.Status.CONFIRMED)))
        .order_by("-starts_at")
    )
    confirmed = Booking.objects.filter(event__organizer=request.user, status=Booking.Status.CONFIRMED)
    totals = confirmed.aggregate(seats_total=Sum("seats"), revenue_total=Sum(F("seats") * F("unit_price")))
    stats = {
        "events": request.user.events.count(),
        "upcoming": request.user.events.upcoming().count(),
        "seats_sold": totals["seats_total"] or 0,
        "revenue": totals["revenue_total"] or 0,
    }
    recent_bookings = confirmed.select_related("event", "attendee")[:8]
    return render(request, "events/dashboard.html", {
        "events": events, "stats": stats, "recent_bookings": recent_bookings,
    })


@organizer_required
def event_create(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.organizer = request.user
        event.save()
        messages.success(request, f"“{event.title}” has been created.")
        return redirect(event)
    return render(request, "events/event_form.html", {"form": form})


@organizer_required
def event_update(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    form = EventForm(request.POST or None, request.FILES or None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your changes have been saved.")
        return redirect(event)
    return render(request, "events/event_form.html", {"form": form, "event": event})


@organizer_required
def event_delete(request, slug):
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    if request.method == "POST":
        title = event.title
        event.delete()
        messages.success(request, f"“{title}” has been deleted.")
        return redirect("events:dashboard")
    return render(request, "events/event_confirm_delete.html", {"event": event})


@organizer_required
def event_bookings(request, slug):
    """Attendee list for one of the organizer's own events."""
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    bookings = event.bookings.select_related("attendee")
    return render(request, "events/event_bookings.html", {"event": event, "bookings": bookings})
