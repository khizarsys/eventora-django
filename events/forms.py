from django import forms
from django.utils import timezone

from .models import Category, Event


class EventFilterForm(forms.Form):
    """Search and filter controls on the public event listing."""

    WHEN_CHOICES = [
        ("", "Any date"),
        ("today", "Today"),
        ("week", "Next 7 days"),
        ("month", "Next 30 days"),
    ]
    PRICE_CHOICES = [("", "Any price"), ("free", "Free"), ("paid", "Paid")]

    q = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"placeholder": "Search events, venues or cities"})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, empty_label="All categories", to_field_name="slug"
    )
    when = forms.ChoiceField(choices=WHEN_CHOICES, required=False)
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    price = forms.ChoiceField(choices=PRICE_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title", "category", "description", "starts_at", "ends_at",
            "venue", "city", "banner", "total_seats", "price", "is_published",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "banner": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {"is_published": "Publish this event (visible to attendees)", "price": "Ticket price (PKR)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "is_published":
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"
        self.fields["total_seats"].widget.attrs["min"] = 1
        self.fields["price"].widget.attrs.update({"min": 0, "step": "0.01"})

    def clean_starts_at(self):
        starts_at = self.cleaned_data["starts_at"]
        # Only new events must be in the future; editing an existing event is still allowed.
        if not self.instance.pk and starts_at < timezone.now():
            raise forms.ValidationError("The event must start in the future.")
        return starts_at

    def clean_total_seats(self):
        total_seats = self.cleaned_data["total_seats"]
        if total_seats < 1:
            raise forms.ValidationError("An event needs at least one seat.")
        # Organizers cannot shrink capacity below the seats already booked.
        if self.instance.pk and total_seats < self.instance.seats_booked:
            raise forms.ValidationError(
                f"{self.instance.seats_booked} seats are already booked; capacity cannot be lower than that."
            )
        return total_seats

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean(self):
        cleaned = super().clean()
        starts_at, ends_at = cleaned.get("starts_at"), cleaned.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", "The end time must be after the start time.")
        return cleaned
