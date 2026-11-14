from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role that decides what the user can do on the platform."""

    class Role(models.TextChoices):
        ORGANIZER = "organizer", "Organizer"
        ATTENDEE = "attendee", "Attendee"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATTENDEE)

    @property
    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    @property
    def is_attendee(self):
        return self.role == self.Role.ATTENDEE

    def __str__(self):
        return self.get_full_name() or self.username
