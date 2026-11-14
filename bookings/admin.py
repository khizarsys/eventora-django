from django.contrib import admin, messages
from django.utils import timezone

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "event", "attendee", "seats", "total_display", "status", "created_at")
    list_filter = ("status", "event__category", ("created_at", admin.DateFieldListFilter))
    search_fields = ("reference", "event__title", "attendee__username", "attendee__email")
    autocomplete_fields = ("event", "attendee")
    readonly_fields = ("reference", "created_at", "cancelled_at")
    date_hierarchy = "created_at"
    list_select_related = ("event", "attendee")
    actions = ["mark_cancelled"]

    @admin.display(description="Total")
    def total_display(self, obj):
        return "Free" if not obj.total_price else f"PKR {obj.total_price:,.0f}"

    @admin.action(description="Cancel selected bookings")
    def mark_cancelled(self, request, queryset):
        updated = queryset.filter(status=Booking.Status.CONFIRMED).update(
            status=Booking.Status.CANCELLED, cancelled_at=timezone.now()
        )
        self.message_user(request, f"{updated} booking(s) cancelled.", messages.SUCCESS)
