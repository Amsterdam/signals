#!/usr/bin/env bash
#
# Production release / pre-serve tasks.
#
# Run this once per deployment, AFTER the new image is available and BEFORE
# (or as an init step for) the uwsgi web process starts serving traffic.
# It is safe to run repeatedly: every command here is idempotent.
#
#   bash /app/release.sh
#
set -eux

# Apply database migrations.
python manage.py migrate --noinput

# Create the DatabaseCache table (CACHES['default'] -> 'signals_cache').
# Idempotent: a no-op if the table already exists. Without this the public
# API 500s, because the DRF rate throttle reads/writes this cache on every
# request (see signals/throttling.py).
python manage.py createcachetable
