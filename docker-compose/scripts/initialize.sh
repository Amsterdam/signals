#!/bin/bash

set -eux

# Apply all migrations
python manage.py migrate --noinput

# Create the super user if it does not exists
echo "Creating the super user if it does not already exists"
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='signals.admin@example.com').exists() or User.objects.create_superuser('signals.admin@example.com', 'signals.admin@example.com', 'password')"

# Collect static
python manage.py collectstatic --no-input

# Create cache table
python manage.py createcachetable

if [[ ${INITIALIZE_WITH_DUMMY_DATA:-0} == 1 ]]; then
  if python manage.py shell -c "import sys; from django.db import connection; cursor = connection.cursor(); cursor.execute('select count(*) from signals_signal'); sys.exit(cursor.fetchone()[0])"; then
    echo "Load dummy data"
    python manage.py load_areas stadsdeel
    python manage.py load_areas cbs-gemeente-2022
    python manage.py load_areas sia-stadsdeel
    python manage.py dummy_sources --to-create 10
    python manage.py dummy_signals --to-create 100
  fi
fi

uwsgi --master \
  --http=0.0.0.0:8000 \
  --callable=application \
  --module=signals.wsgi:application \
  --static-index=index.html \
  --static-map=/signals/static=/app/static \
  --static-map=/signals/media=/app/media \
  --buffer-size=8192 \
  --harakiri=15 \
  --py-auto-reload=1 \
  --lazy-apps \
  --die-on-term
