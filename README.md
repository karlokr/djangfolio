# Portfolio Site

A Django-based portfolio website with resume and project showcase sections, containerized with Docker.

## Features

- **Responsive Design**: Works on desktop and high-resolution displays (2K/4K)
- **Project Portfolio**: Showcase your projects with images, videos, and PDFs
- **Resume Section**: Display your experience, education, and skills
- **Contact Form**: Working email contact form with SMTP support
- **GitHub Integration**: Automatically fetches and displays your GitHub repositories
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Node.js and npm (for local development)

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure your settings:
   - `SECRET_KEY`: Generate a new Django secret key for production
   - Email settings for contact form functionality
   - `DEBUG`: Set to `False` in production
   - `ALLOWED_HOSTS`: Add your domain names (comma-separated)
   - `CSRF_TRUSTED_ORIGINS`: Add your HTTPS URLs (required for production with HTTPS)
     - Example: `https://example.com,https://www.example.com`

### Running with Docker

1. **Install npm dependencies** (first time only):
   ```bash
   npm install
   ```
   This installs Bootstrap, jQuery, and other frontend dependencies from `package.json` into `node_modules/`.

2. **Create the database directory** (first time only):
   ```bash
   mkdir -p db
   touch db/db.sqlite3
   chmod 666 db/db.sqlite3
   ```

3. **Build and start the container**:
   ```bash
   docker compose up --build -d
   ```

4. **Run migrations** (first time only):
   ```bash
   docker compose exec web python manage.py makemigrations
   docker compose exec web python manage.py migrate
   ```

5. **Collect static files** (first time only):
   ```bash
   docker compose exec web python manage.py collectstatic --noinput
   ```
   This copies static files from `node_modules/` and app directories into `staticfiles/` for serving.

6. **Create an admin user** (first time only):
   ```bash
   docker compose exec web python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@localhost', 'admin')"
   ```
   Default credentials: `admin` / `admin` (change after first login!)

7. **Access the site**:
   - Main site: `http://localhost:8888`
   - Admin panel: `http://localhost:8888/admin`

8. **View logs**:
   ```bash
   docker compose logs -f web
   ```

9. **Stop the container**:
   ```bash
   docker compose down
   ```

**Note**: 
- The database file is stored in the `db/` directory (`db/db.sqlite3`) on your host machine and persists between container restarts
- Static files are collected into `staticfiles/` and served by Django in development mode
- The development server auto-reloads when you make changes to Python files or templates - no need to restart!
- For production deployment, use Gunicorn (configured in Dockerfile) instead of the development server

## Site Configuration

The site uses a database-backed configuration system for personal information (name, email, social media links, etc.) instead of hardcoding values in templates.

### Configuring Your Site

After initial setup, you can customize your site information via the admin panel:

1. **Via Django Admin** (recommended):
   - Go to `http://localhost:8888/admin`
   - Login with admin credentials
   - Click on "Site Configurations"
   - Edit the single configuration entry
   - Update your name, emails, GitHub username, LinkedIn username, etc.

### Configuration Fields

- `full_name`: Your full name displayed on the site
- `contact_email`: Email where contact form messages are sent
- `display_email`: Email address shown publicly on the site
- `github_username`: Your GitHub username (for API integration)
- `github_url`: Full URL to your GitHub profile
- `linkedin_username`: Your LinkedIn username
- `linkedin_url`: Full URL to your LinkedIn profile
- `copyright_text`: Copyright text in the footer
- `profile_image`: Upload your profile photo (optional, recommended size: 400x400px or larger, square aspect ratio)
- `profile_image_alt_text`: Alt text for your profile image (accessibility)

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

## Email Configuration

The contact form supports SMTP email sending. Configure these environment variables in `.env`:

- `EMAIL_HOST`: Your SMTP server
- `EMAIL_PORT`: SMTP port (usually 465 for SSL)
- `EMAIL_HOST_USER`: Your email address
- `EMAIL_HOST_PASSWORD`: Your email password or app-specific password
- `EMAIL_SSL_VERIFY`: SSL certificate verification (default: `True`)
  - Set to `True` for production (recommended - verifies SSL certificates)
  - Set to `False` only for development/testing with self-signed certificates
  - **Warning**: Disabling verification reduces security

## Docker Hub Image

The portfolio site is available as a pre-built Docker image on Docker Hub:

```bash
# Pull the latest version
docker pull karlokr94/portfolio-site:latest

# Or pull a specific version
docker pull karlokr94/portfolio-site:v1.0.0
```

## Production Deployment

### Prerequisites for Production

- Docker and Docker Compose installed
- A domain name configured to point to your server
- SSL/TLS certificates (recommended: Let's Encrypt via Traefik or similar)
- Email SMTP credentials for contact form

### Production Docker Compose Example

Create a `docker-compose.yml` file for production deployment:

```yaml
services:
  portfolio:
    image: karlokr94/portfolio-site:latest
    container_name: portfolio-site
    restart: unless-stopped
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_PORT=${EMAIL_PORT}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - EMAIL_USE_SSL=True
      - EMAIL_SSL_VERIFY=True
    volumes:
      - ./db:/app/db
      - ./media:/app/media
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Production Environment Variables

Create a `.env` file with production values:

```bash
# Django Settings
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
EMAIL_USE_SSL=True
EMAIL_SSL_VERIFY=True
```

### Important Production Configuration Notes

1. **ALLOWED_HOSTS**: Controls which HTTP Host headers Django accepts
   - Must include all domains/subdomains serving your site
   - Example: `yourdomain.com,www.yourdomain.com`

2. **CSRF_TRUSTED_ORIGINS**: Required for HTTPS deployments with reverse proxy
   - Must include the protocol (`https://`)
   - Must match domains users will access
   - Example: `https://yourdomain.com,https://www.yourdomain.com`

3. **SECRET_KEY**: Generate a new one for production
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

4. **Database and Media Volumes**:
   - Mount `./db:/app/db` to persist database (database file will be at `./db/db.sqlite3`)
   - Mount `./media:/app/media` to persist uploaded files
   - Ensure proper file permissions on the host

### Reverse proxy

- Can be used with any reverse proxy such as nginx or traefik

## Security Notes

- Never commit `.env` file to version control
- Generate a new `SECRET_KEY` for production
- Use environment-specific email credentials
- Set `DEBUG=False` in production
- Configure proper `ALLOWED_HOSTS` for your domain

## Recent Updates

- Fixed high-resolution display scrolling issue on portfolio tab
- Implemented working Django-based email contact form
- Added support for self-signed SSL certificates in email
- Dockerized deployment with proper static file handling
- Fixed PDF modal display with X-Frame-Options configuration
