#!/bin/sh
# migracje przed startem serwera
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting gunicorn..."
exec "$@"
