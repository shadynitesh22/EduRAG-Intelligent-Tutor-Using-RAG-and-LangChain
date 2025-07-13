#!/bin/bash

# Exit on any error
set -e

echo "Starting EduRAG application..."

# Wait for database to be ready
echo "Waiting for database..."
until python manage.py shell -c "from django.db import connections; connections['default'].cursor()" 2>/dev/null; do
    echo "Database is unavailable - sleeping"
    sleep 1
done

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Setup default data (subjects, grades, admin user)
echo "Setting up default data..."
python manage.py setup_default_data

# Start the application
echo "Starting Gunicorn..."
exec gunicorn rag_tutor.wsgi:application --bind 0.0.0.0:8000 --workers 4 