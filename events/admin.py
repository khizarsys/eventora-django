from django.contrib import admin
from django.utils.html import format_html

from bookings.models import Booking

from .models import Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "event_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Events")
    def event_count(self, obj):
        return obj.events.count()


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ("reference", "attendee", "seats", "unit_price", "status", "created_at")
    readonly_fields = ("reference", "created_at")
    autocomplete_fields = ("attendee",)
    show_change_link = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "organizer", "starts_at", "city", "price_display", "seats_display", "is_published")
    list_filter = ("is_published", "category", "city", ("starts_at", admin.DateFieldListFilter))
    list_editable = ("is_published",)
    search_fields = ("title", "description", "venue", "city", "organizer__username", "organizer__email")
    date_hierarchy = "starts_at"
    autocomplete_fields = ("organizer", "category")
    readonly_fields = ("slug", "created_at", "updated_at", "banner_preview")
    inlines = [BookingInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "organizer", "category", "description", "is_published")}),
        ("Schedule & venue", {"fields": ("starts_at", "ends_at", "venue", "city")}),
        ("Tickets", {"fields": ("total_seats", "price")}),
        ("Media", {"fields": ("banner", "banner_preview")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "organizer").with_seats_booked()

    @admin.display(description="Price", ordering="price")
    def price_display(self, obj):
        return "Free" if obj.is_free else f"PKR {obj.price:,.0f}"

    @admin.display(description="Seats booked")
    def seats_display(self, obj):
        return f"{obj.seats_booked} / {obj.total_seats}"

    @admin.display(description="Banner preview")
    def banner_preview(self, obj):
        if obj.banner:
            return format_html('<img src="{}" style="max-height:160px;border-radius:8px;">', obj.banner.url)
        return "No banner uploaded"
