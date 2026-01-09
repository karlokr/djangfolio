# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=portfolio.settings \
    DEBUG=False \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libxcb1-dev \
        nodejs \
        npm \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files and install npm dependencies
COPY package.json package-lock.json* ./
RUN npm install --production

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN addgroup --system django \
    && adduser --system --ingroup django django

# Copy project files (including existing media uploads)
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create staticfiles directory and ensure media directory exists with proper permissions
# Note: In production, consider using external storage (e.g., AWS S3) for media files
RUN mkdir -p /app/staticfiles \
    && chown -R django:django /app \
    && chmod -R 755 /app \
    && if [ -f /app/db.sqlite3 ]; then chmod 664 /app/db.sqlite3; fi

# The existing media/ and db.sqlite3 files are already copied with COPY . .

# Collect static files (DEBUG=false is set in ENV above)
RUN python manage.py collectstatic --noinput --clear

# NOTE: Running as root for now to avoid SQLite permission issues with mounted volumes
# In production, consider using PostgreSQL and running as non-root user
# USER django

# Expose port
EXPOSE 8000

# Health check
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/ || exit 1

# Set entrypoint and default command
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "portfolio.wsgi:application"]
