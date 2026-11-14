from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def organizer_required(view_func):
    """Allow access only to logged-in users with the Organizer role."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_organizer:
            messages.error(request, "Only organizers can access that page.")
            return redirect("events:list")
        return view_func(request, *args, **kwargs)

    return wrapper


def attendee_required(view_func):
    """Allow access only to logged-in users with the Attendee role."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_attendee:
            messages.error(request, "Only attendee accounts can book seats.")
            return redirect("events:list")
        return view_func(request, *args, **kwargs)

    return wrapper
