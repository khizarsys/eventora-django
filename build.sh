#!/usr/bin/env bash
# Render build script: install dependencies, collect static files, migrate,
# and optionally create an admin user and demo data.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Creates the admin account from DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD
# when they are set. Ignored if the user already exists.
if [[ -n "$DJANGO_SUPERUSER_USERNAME" ]]; then
  python manage.py createsuperuser --no-input || echo "Superuser already exists, skipping."
fi

# Seeds demo events on the first deploy; on later deploys it only restores
# banner images (Render's free tier has no persistent disk).
if [[ "${SEED_DEMO_DATA,,}" == "true" ]]; then
  python manage.py seed_events
fi
