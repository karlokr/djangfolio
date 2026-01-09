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
   - `ALLOWED_HOSTS`: Add your domain names

### Running with Docker

1. **Install npm dependencies** (first time only):
   ```bash
   npm install
   ```
   This installs Bootstrap, jQuery, and other frontend dependencies from `package.json` into `node_modules/`.

2. **Create the database file** (first time only):
   ```bash
   touch db.sqlite3
   chmod 666 db.sqlite3
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
- The database file (`db.sqlite3`) is stored on your host machine and persists between container restarts
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
