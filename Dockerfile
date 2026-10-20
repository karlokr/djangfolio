# Use Python 3.12 slim image as base, pinned by digest so every build uses the
# exact same image. Dependabot (docker ecosystem) proposes digest updates.
FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170

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
# npm ci installs exactly what package-lock.json records (and fails if it
# doesn't match package.json).
RUN npm ci --omit=dev

# Copy requirements and install Python dependencies
COPY requirements.txt .
# requirements.txt is compiled from requirements.in with exact versions and
# hashes; --require-hashes rejects any package that doesn't match.
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

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
# settings.py refuses to start without SECRET_KEY when DEBUG is off, so give
# this build-only step a throwaway key. The real key comes from the runtime env.
RUN SECRET_KEY=collectstatic-build-only-not-secret python manage.py collectstatic --noinput --clear

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
