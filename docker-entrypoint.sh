#!/bin/bash
set -e

echo "🔄 Starting Django Portfolio Site..."

# For SQLite, ensure the database file and directory are writable
if [ -f /app/db.sqlite3 ]; then
    echo "📁 Setting database permissions..."
    chmod 664 /app/db.sqlite3 || echo "⚠️  Could not set db.sqlite3 permissions (may need to run as root)"
fi

# Ensure the app directory is writable (for SQLite lock files)
chmod 755 /app || echo "⚠️  Could not set /app permissions (may need to run as root)"

echo "📊 Running database migrations..."

# Create migrations if needed
python manage.py makemigrations --noinput

# Apply migrations
python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

echo "🚀 Starting application..."

# Execute the main command (usually gunicorn)
exec "$@"