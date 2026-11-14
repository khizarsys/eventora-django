from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.my_bookings, name="my_bookings"),
    path("book/<slug:slug>/", views.create_booking, name="create"),
    path("<str:reference>/", views.booking_confirmation, name="confirmation"),
    path("<str:reference>/cancel/", views.cancel, name="cancel"),
]
