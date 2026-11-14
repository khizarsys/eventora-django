"""
Populate the database with realistic demo data.

    python manage.py seed_events           # add demo data (skips if already seeded)
    python manage.py seed_events --reset   # wipe demo events/bookings and recreate them

Creates categories, 3 organizers, 6 attendees, 15 upcoming events with
generated banner images, and a spread of bookings so dashboards look alive.
"""

import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter

from accounts.models import User
from bookings.models import Booking
from events.models import Category, Event

DEMO_PASSWORD = "Eventora@123"

CATEGORIES = [
    # name, Bootstrap icon, banner gradient colours
    ("Music", "bi-music-note-beamed", ("#3a1c71", "#d76d77")),
    ("Technology", "bi-cpu", ("#0f2027", "#2c5364")),
    ("Business", "bi-briefcase", ("#1e3c72", "#2a5298")),
    ("Food & Drink", "bi-cup-hot", ("#b24592", "#f15f79")),
    ("Sports", "bi-trophy", ("#134e5e", "#71b280")),
    ("Arts & Culture", "bi-palette", ("#8e2de2", "#4a00e0")),
    ("Workshops", "bi-tools", ("#c94b4b", "#4b134f")),
]

ORGANIZERS = [
    ("ayesha.events", "Ayesha", "Malik", "ayesha@eventora.demo"),
    ("techhub.pk", "Hamza", "Qureshi", "hamza@eventora.demo"),
    ("lahore.live", "Sana", "Iqbal", "sana@eventora.demo"),
]

ATTENDEES = [
    ("ali.raza", "Ali", "Raza", "ali@eventora.demo"),
    ("fatima.khan", "Fatima", "Khan", "fatima@eventora.demo"),
    ("usman.tariq", "Usman", "Tariq", "usman@eventora.demo"),
    ("zainab.ahmed", "Zainab", "Ahmed", "zainab@eventora.demo"),
    ("bilal.hussain", "Bilal", "Hussain", "bilal@eventora.demo"),
    ("maryam.shah", "Maryam", "Shah", "maryam@eventora.demo"),
]

# title, category, organizer index, days from now, start hour, duration (h), venue, city, seats, price (PKR)
EVENTS = [
    ("Lahore Music Festival", "Music", 2, 12, 18, 6, "Expo Centre Lahore", "Lahore", 800, 3500,
     "A full evening of live performances from Pakistan's top indie, pop and Sufi rock artists across two stages.\n\n"
     "Food trucks, merch stalls and a dedicated chill-out zone are included with every ticket."),
    ("Sufi Night at the Fort", "Music", 2, 26, 20, 3, "Lahore Fort, Diwan-e-Aam", "Lahore", 300, 2500,
     "An intimate qawwali evening under the stars in the historic courtyard of Lahore Fort.\n\n"
     "Seating is on traditional floor cushions; please arrive 30 minutes early for security checks."),
    ("Karachi Jazz Evening", "Music", 0, 40, 19, 3, "Arts Council of Pakistan", "Karachi", 220, 2000,
     "Smooth jazz, soul and blues from local and visiting musicians in the Arts Council auditorium."),
    ("Pakistan DevCon", "Technology", 1, 9, 9, 8, "National Incubation Center", "Islamabad", 450, 0,
     "The largest community-run developer conference in the country: talks on cloud, AI, mobile and open source.\n\n"
     "Free entry with registration. Lunch and swag provided for all attendees."),
    ("AI for Startups Bootcamp", "Technology", 1, 18, 10, 6, "Arfa Software Technology Park", "Lahore", 60, 4500,
     "A hands-on, one-day bootcamp on shipping AI features: prompt design, retrieval, evaluation and cost control.\n\n"
     "Bring a laptop. Suitable for developers and technical founders."),
    ("Cloud Native Meetup: Kubernetes in Production", "Technology", 1, 5, 17, 2, "Daftarkhwan One", "Karachi", 80, 0,
     "Engineers from local unicorns share lessons learned running Kubernetes at scale. Networking and chai afterwards."),
    ("Women in Tech Leadership Summit", "Business", 0, 21, 10, 7, "Serena Hotel", "Islamabad", 250, 3000,
     "Keynotes, panels and mentorship circles celebrating women leading engineering, product and design teams."),
    ("Startup Pitch Night", "Business", 1, 15, 18, 3, "Plan9 Incubator", "Lahore", 120, 500,
     "Ten early-stage startups pitch to a panel of investors. Vote for the audience award and meet the founders."),
    ("Karachi Food Carnival", "Food & Drink", 2, 30, 16, 7, "Beach View Park, Clifton", "Karachi", 1500, 800,
     "Over 60 food stalls, live cooking stations and dessert alleys by the sea. Family-friendly with a kids' zone."),
    ("Specialty Coffee Tasting Workshop", "Food & Drink", 0, 7, 11, 2, "Coffee Wagera, Gulberg", "Lahore", 25, 2800,
     "Learn to taste like a barista: cupping, brew methods and latte art with a certified Q grader."),
    ("Islamabad Half Marathon", "Sports", 2, 45, 6, 4, "F-9 Fatima Jinnah Park", "Islamabad", 2000, 1500,
     "A scenic 21 km route through the capital with 5 km and 10 km options. Medal and timing chip included."),
    ("Corporate Cricket Cup", "Sports", 0, 34, 14, 5, "Gaddafi Stadium Practice Ground", "Lahore", 400, 0,
     "Eight corporate teams battle it out in a T10 tournament. Free entry for spectators with registration."),
    ("Contemporary Art Exhibition: New Voices", "Arts & Culture", 0, 3, 12, 8, "Alhamra Art Gallery", "Lahore", 500, 0,
     "A curated showcase of emerging Pakistani artists working in painting, sculpture and digital media."),
    ("Urdu Poetry Mushaira", "Arts & Culture", 2, 23, 20, 3, "PNCA Auditorium", "Islamabad", 350, 1000,
     "An evening of classical and contemporary Urdu poetry with renowned poets from across the country."),
    ("UI/UX Design Masterclass", "Workshops", 1, 11, 10, 5, "Colabs", "Lahore", 40, 6000,
     "From wireframes to polished prototypes in Figma. Includes portfolio review and a certificate of completion."),
]


class Command(BaseCommand):
    help = "Seed the database with realistic demo events, users and bookings."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data before seeding.")

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        demo_emails = [u[3] for u in ORGANIZERS + ATTENDEES]

        if reset:
            for event in Event.objects.filter(organizer__email__in=demo_emails).exclude(banner=""):
                event.banner.delete(save=False)  # remove the image file, not just the DB row
            deleted, _ = User.objects.filter(email__in=demo_emails).delete()
            self.stdout.write(self.style.WARNING(f"Removed existing demo data ({deleted} rows)."))
        elif Event.objects.filter(organizer__email__in=demo_emails).exists():
            self.stdout.write("Demo data already exists. Use --reset to recreate it.")
            return

        random.seed(42)  # repeatable demo data
        categories = self._create_categories()
        organizers = [self._create_user(*data, role=User.Role.ORGANIZER) for data in ORGANIZERS]
        attendees = [self._create_user(*data, role=User.Role.ATTENDEE) for data in ATTENDEES]
        events = self._create_events(categories, organizers)
        bookings = self._create_bookings(events, attendees)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(categories)} categories, {len(organizers)} organizers, "
            f"{len(attendees)} attendees, {len(events)} events and {bookings} bookings."
        ))
        self.stdout.write(f"Demo password for all demo accounts: {DEMO_PASSWORD}")
        self.stdout.write(f"  Organizer: {ORGANIZERS[0][0]}   Attendee: {ATTENDEES[0][0]}")

    def _create_categories(self):
        categories = {}
        for name, icon, colors in CATEGORIES:
            category, _ = Category.objects.update_or_create(name=name, defaults={"icon": icon})
            category.colors = colors
            categories[name] = category
        return categories

    def _create_user(self, username, first_name, last_name, email, role):
        user = User.objects.create_user(
            username=username, email=email, password=DEMO_PASSWORD,
            first_name=first_name, last_name=last_name, role=role,
        )
        return user

    def _create_events(self, categories, organizers):
        today = timezone.localtime().replace(minute=0, second=0, microsecond=0)
        events = []
        for (title, cat_name, org_idx, days, hour, duration, venue, city, seats, price, description) in EVENTS:
            starts_at = (today + timedelta(days=days)).replace(hour=hour)
            category = categories[cat_name]
            event = Event(
                organizer=organizers[org_idx], category=category, title=title, description=description,
                starts_at=starts_at, ends_at=starts_at + timedelta(hours=duration),
                venue=venue, city=city, total_seats=seats, price=price,
            )
            event.save()
            event.banner.save(f"{event.slug}.jpg", ContentFile(make_banner(title, cat_name, category.colors)), save=True)
            events.append(event)
        return events

    def _create_bookings(self, events, attendees):
        count = 0
        for event in events:
            # Fill each event to a different level so the dashboard shows variety.
            for attendee in random.sample(attendees, k=random.randint(2, len(attendees))):
                seats = min(random.randint(1, 4), event.seats_left)
                if seats < 1:
                    break
                Booking.objects.create(event=event, attendee=attendee, seats=seats, unit_price=event.price)
                count += 1
        # Nearly sell out the smallest workshop to demo the "only a few seats left" badge.
        coffee = next(e for e in events if e.total_seats == 25)
        remaining = coffee.seats_left - 3
        while remaining > 0:
            seats = min(4, remaining)
            Booking.objects.create(event=coffee, attendee=random.choice(attendees), seats=seats, unit_price=coffee.price)
            remaining -= seats
            count += 1
        # One cancelled booking for the "Cancelled" tab.
        to_cancel = Booking.objects.filter(attendee=attendees[0]).order_by("pk").last()
        if to_cancel:
            to_cancel.status = Booking.Status.CANCELLED
            to_cancel.cancelled_at = timezone.now()
            to_cancel.save(update_fields=["status", "cancelled_at"])
        return count


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def make_banner(title, category, colors, size=(1280, 720)):
    """
    Generate a 16:9 abstract banner: diagonal gradient, soft light blobs and a
    dotted grid. No text is drawn, so cards and the detail page can overlay
    badges and titles without clashing with the artwork.
    """
    width, height = size
    start, end = _hex_to_rgb(colors[0]), _hex_to_rgb(colors[1])

    # Draw the gradient on a small canvas and upscale it: smooth and fast.
    small_w, small_h = 64, 36
    gradient = Image.new("RGB", (small_w, small_h))
    for x in range(small_w):
        for y in range(small_h):
            t = (x / small_w) * 0.7 + (y / small_h) * 0.3
            gradient.putpixel((x, y), tuple(int(start[i] + (end[i] - start[i]) * t) for i in range(3)))
    image = gradient.resize(size, Image.Resampling.BICUBIC).convert("RGBA")

    # Soft light blobs, positioned deterministically per event title.
    rng = random.Random(f"{category}:{title}")
    blobs = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(blobs)
    for _ in range(7):
        r = rng.randint(90, 300)
        cx, cy = rng.randint(0, width), rng.randint(0, height)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, rng.randint(16, 38)))
    image = Image.alpha_composite(image, blobs.filter(ImageFilter.GaussianBlur(10)))

    # Dotted grid in one corner and a couple of thin rings for texture.
    detail = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(detail)
    for gx in range(width - 340, width - 60, 28):
        for gy in range(60, 300, 28):
            draw.ellipse((gx - 3, gy - 3, gx + 3, gy + 3), fill=(255, 255, 255, 70))
    for _ in range(2):
        r = rng.randint(140, 260)
        cx, cy = rng.randint(0, width // 2), rng.randint(height // 2, height)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 60), width=4)
    image = Image.alpha_composite(image, detail)

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()
