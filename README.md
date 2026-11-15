# Eventora

**Discover, publish and book events, all in one place.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-production-4169E1?logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=black)
![Tests](https://img.shields.io/badge/tests-37%20passing-success)

### 🔗 [Live demo: eventora-2usq.onrender.com](https://eventora-2usq.onrender.com/)

> Hosted on Render's free plan, so the first visit after a period of inactivity can take about a minute to wake up.
> Try it with the demo accounts: organizer `ayesha.events` / attendee `ali.raza` (password `Eventora@123`).

Eventora is a full-stack event management and booking platform built with Django. Organizers publish events and track their bookings. Attendees browse, search and reserve seats, and the system makes sure no event is ever overbooked.

---

## About the project

Small event organizers (meetups, workshops, concerts, community festivals) often run registrations through spreadsheets, social media messages and paper lists. Seats get double-booked, attendees lose track of their tickets, and organizers have no clear view of how full an event is.

Eventora puts the whole flow in one place:

- **Organizers** create events with a banner, venue, capacity and price, then follow bookings and remaining seats from a dashboard.
- **Attendees** find events by keyword, category, date or price, book seats in two clicks, get a confirmation with a booking reference, and can cancel at any time before the event starts.
- **Capacity is enforced at the database level.** The booking service locks the event row while it checks availability, so two people booking the last seats at the same moment cannot both succeed.

## Features

**Accounts and roles**
- Sign up, log in and log out, with a choice of **Organizer** or **Attendee** role at signup
- Role-based access: only organizers can manage events, and only attendees can book

**For organizers**
- Create, edit and delete events: title, description, category, start/end date and time, venue, city, banner image, total seats, and a price (or free)
- Save events as drafts that stay hidden until published
- Dashboard with total events, upcoming events, seats booked and revenue
- Per-event table showing bookings, seats booked and seats left, with an occupancy bar
- Attendee list for each event (reference, name, email, seats, status)
- Capacity cannot be reduced below the number of seats already booked

**For attendees**
- Browse upcoming events in a responsive card grid with pagination
- Search by keyword (title, description, venue, city)
- Filter by category, date range (today / next 7 days / next 30 days), exact date and free/paid
- Event detail page with live seat availability and related events
- Book 1–10 seats per booking, with **overbooking prevention**
- Booking confirmation page with a unique reference (e.g. `EVT-7K2Q9M`)
- Confirmation email (printed to the console in development)
- "My Bookings" page with Upcoming / Past / Cancelled tabs, and cancellation until the event starts

**Admin and tooling**
- Customized Django admin with list filters, search, date hierarchy, inline bookings, banner previews and a bulk "cancel bookings" action
- `python manage.py seed_events` creates 15 realistic events, demo users, generated banner images and bookings
- 37 automated tests covering booking rules, cancellation, permissions and views
- One-click deployment to Render with `render.yaml`

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Django 5.2 |
| Database | PostgreSQL in production, SQLite locally (via `dj-database-url`) |
| Frontend | Django templates, Bootstrap 5.3, Bootstrap Icons, Inter font |
| Media | Pillow (banner uploads and generated demo banners) |
| Config | `python-dotenv` |
| Serving | Gunicorn, WhiteNoise (compressed, hashed static files) |
| Hosting | Render (web service and managed PostgreSQL) |

## Screenshots

> Screenshots live in the [`screenshots/`](screenshots/) folder.

| Home and search | Event details |
|---|---|
| ![Home page](screenshots/home.png) | ![Event detail](screenshots/event-detail.png) |

| Booking confirmation | My bookings |
|---|---|
| ![Booking confirmation](screenshots/booking-confirmation.png) | ![My bookings](screenshots/my-bookings.png) |

| Organizer dashboard | Create event |
|---|---|
| ![Organizer dashboard](screenshots/dashboard.png) | ![Create event](screenshots/create-event.png) |

| Django admin | Mobile view |
|---|---|
| ![Admin](screenshots/admin.png) | ![Mobile](screenshots/mobile.png) |

## Folder structure

```
eventora-django/
├── eventora/                 # Project settings, root URLs, WSGI/ASGI
├── accounts/                 # Custom User model (roles), signup/login, role decorators
├── events/                   # Category & Event models, listing/search, organizer CRUD & dashboard
│   └── management/commands/
│       └── seed_events.py    # Demo data generator
├── bookings/                 # Booking model, booking service (overbooking protection), views
│   └── services.py           # book_seats() / cancel_booking(): all booking rules live here
├── templates/                # Base layout, partials, and per-app templates
│   ├── accounts/  events/  bookings/  partials/
│   └── emails/               # Plain-text confirmation email
├── static/                   # Custom CSS theme and favicon
├── screenshots/              # README images
├── build.sh                  # Render build script
├── render.yaml               # Render Blueprint (web service + PostgreSQL)
├── requirements.txt
├── .env.example
└── manage.py
```

## How to run locally

**Prerequisites:** Python 3.11 or newer and Git.

1. **Clone the repository**
   ```bash
   git clone https://github.com/khizarsys/eventora-django.git
   cd eventora-django
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file**
   ```bash
   # Windows
   copy .env.example .env
   # macOS / Linux
   cp .env.example .env
   ```
   The defaults work out of the box with SQLite. For anything beyond local testing, set your own `SECRET_KEY`.

5. **Set up the database and demo data**
   ```bash
   python manage.py migrate
   python manage.py seed_events
   python manage.py createsuperuser   # optional, for /admin
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```
   Open http://127.0.0.1:8000.

7. **Log in with a demo account** (created by `seed_events`)

   | Role | Username | Password |
   |---|---|---|
   | Organizer | `ayesha.events` | `Eventora@123` |
   | Attendee | `ali.raza` | `Eventora@123` |

   Other demo users: organizers `techhub.pk` and `lahore.live`; attendees `fatima.khan`, `usman.tariq`, `zainab.ahmed`, `bilal.hussain` and `maryam.shah` (same password). These accounts are for demonstration only.

8. **Run the tests**
   ```bash
   python manage.py test
   ```

Useful commands:

```bash
python manage.py seed_events --reset   # wipe and recreate demo data
```

When you book a seat locally, the confirmation email is printed in the terminal running `runserver`.

## Environment variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes (production) | dev-only key | Django secret key. Use a long random string in production. |
| `DEBUG` | No | `False` | `True` for local development. Always `False` in production. |
| `ALLOWED_HOSTS` | No | `127.0.0.1,localhost` | Comma-separated host names. The Render hostname is added automatically. |
| `DATABASE_URL` | No | SQLite file | PostgreSQL URL, e.g. `postgres://user:pass@host:5432/db`. Empty means SQLite. |
| `CSRF_TRUSTED_ORIGINS` | No | – | Comma-separated origins for custom domains, e.g. `https://events.example.com`. |
| `DEFAULT_FROM_EMAIL` | No | `Eventora <no-reply@eventora.local>` | Sender address for confirmation emails. |
| `EMAIL_BACKEND` | No | console backend | Set to an SMTP backend to send real emails. |
| `SERVE_MEDIA` | No | `True` | Serve uploaded banners from Django (fine for a demo). |

Used only by the Render build script:

| Variable | Description |
|---|---|
| `SEED_DEMO_DATA` | `True` runs `seed_events` on every deploy. It seeds once, then only restores missing banners. |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | When set, an admin account is created during the build. |

## Deployment (Render)

The repository includes a [Render Blueprint](render.yaml) that provisions a **web service** and a **PostgreSQL database** on the free plan.

1. Sign in to [Render](https://render.com) and connect your GitHub account.
2. Click **New → Blueprint** and select the `eventora-django` repository.
3. Render reads `render.yaml` and asks for the values marked `sync: false`. Enter:
   - `DJANGO_SUPERUSER_USERNAME`: your admin username
   - `DJANGO_SUPERUSER_EMAIL`: your admin email
   - `DJANGO_SUPERUSER_PASSWORD`: a strong password
4. Click **Apply**. Render creates the database and runs `build.sh` (install, `collectstatic`, `migrate`, create admin, seed demo data), then starts Gunicorn.
5. Open the service URL (this project runs at https://eventora-2usq.onrender.com). The admin lives at `/admin`.

These variables are set automatically by the Blueprint, so you don't need to add them yourself:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Linked from the `eventora-db` database |
| `SECRET_KEY` | Generated by Render |
| `DEBUG` | `False` |
| `PYTHON_VERSION` | `3.12.7` |
| `SEED_DEMO_DATA` | `True` (set it to `False` once you have real data) |

**Notes about the free plan**
- The free web service sleeps after 15 minutes of inactivity, so the first request afterwards takes about a minute.
- The free web service has no persistent disk. Banners uploaded through the app are lost on redeploy. Demo banners are regenerated automatically. For real use, store media in S3 or Cloudinary.
- Free PostgreSQL databases on Render expire after a limited period. Check Render's current free-tier terms and upgrade the database if the site needs to stay up.

## Design decisions

- **Custom user model with a `role` field** instead of Django groups. Two fixed roles are simpler to reason about and check (`user.is_organizer`).
- **Booking rules live in `bookings/services.py`**, not in views, so they are easy to test and reuse (from views, admin or a future API).
- **Overbooking protection** uses `select_for_update()` inside a transaction. On PostgreSQL this locks the event row during the availability check. SQLite serializes writes on its own.
- **Seat counts are calculated** from confirmed bookings, not stored in a counter, so they can never drift out of sync. Lists use a single annotated query to avoid N+1 queries.
- **Price is copied to the booking** (`unit_price`) when it is made, so later price changes don't affect existing bookings.
- **Payments are out of scope.** Paid events show "payment collected at the venue". Currency is PKR and the time zone is `Asia/Karachi`.
- **Logout is POST-only**, in line with Django 5 and to protect against CSRF.
- **Demo banners are generated with Pillow**, so the project needs no external image assets or licensing.

## Future improvements

- Online payments (Stripe or a local gateway such as JazzCash or Easypaisa)
- QR-code tickets and an organizer check-in screen
- Waitlists for sold-out events
- Multiple ticket tiers (VIP, early bird, student) and promo codes
- HTML email templates and reminder emails before events
- Cloud media storage (S3 or Cloudinary) for banners
- REST API (Django REST Framework) for a mobile app
- Event reviews and ratings, plus calendar (`.ics`) export
- Password reset and email verification
- CSV export of attendee lists

## Author

**Khizar Hayat**, BS Software Engineering, Riphah International University
LinkedIn: [linkedin.com/in/khizar-hayat-dev](https://www.linkedin.com/in/khizar-hayat-dev)
