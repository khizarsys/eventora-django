from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("events/new/", views.event_create, name="create"),
    path("events/<slug:slug>/", views.event_detail, name="detail"),
    path("events/<slug:slug>/edit/", views.event_update, name="update"),
    path("events/<slug:slug>/delete/", views.event_delete, name="delete"),
    path("events/<slug:slug>/bookings/", views.event_bookings, name="bookings"),
]
