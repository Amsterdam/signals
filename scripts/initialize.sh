#!/bin/bash

# Wait for database to be up
RETRIES=30
until nc database 5432 || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
  sleep 2
done

# If there is already a log file there is no need to initialize the database
# and load dummy data for now
LOGFILE='/app/initialize.log'

if [[ ! -f "$LOGFILE" ]]; then
  echo "Start with a fresh database"
  export PGPASSWORD=insecure
  psql -h database -p 5432 -d signals -U signals -c "drop schema public cascade;"
  psql -h database -p 5432 -d signals -U signals -c "create schema public;"
fi

# Apply all migrations
python manage.py migrate --noinput

# Create the super user if it does not exists
echo "Creating the super user if it does not already exists"
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='signals.admin@example.com').exists() or User.objects.create_superuser('signals.admin@example.com', 'signals.admin@example.com', 'password')" | python manage.py shell

# Collect static
python manage.py collectstatic --no-input

if [[ ! -f "$LOGFILE" ]]; then
  echo "Load dummy data"
  python manage.py load_areas stadsdeel
  python manage.py load_areas cbs-gemeente-2019
  python manage.py load_areas sia-stadsdeel

  # Other scripts to load data should be placed here
  # python manage.py dummy_categories --parents-to-create 10 --children-to-create 5 # Disabled because there are already categories loaded through the migrations
  # python manage.py dummy_departments --to-create 10  # Disabled because there are already departments loaded through the migrations
  python manage.py dummy_sources --to-create 10
  python manage.py dummy_signals --to-create 100

  echo "[$(date +"%FT%T%z")] - Done!!!" >> "$LOGFILE"
fi

uwsgi --master \
  --http=0.0.0.0:8000 \
  --callable=application \
  --module=signals.wsgi:application \
  --static-index=index.html \
  --static-map=/signals/static=/static \
  --static-map=/signals/media=/media \
  --harakiri=15 \
  --py-auto-reload=1 \
  --die-on-term
