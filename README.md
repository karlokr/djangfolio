# Djangfolio

A Django-based portfolio website with resume, project showcase, and blog sections, fully containerized for easy deployment. Features SPA-like navigation powered by HTMX for a seamless user experience.

## Features

- **SPA-Like Navigation**: HTMX-powered navigation that updates only the content area while keeping the navbar fixed—no full page reloads
- **Responsive Design**: Optimized for all screen sizes including mobile, tablet, and high-resolution displays (2K/4K)
- **Blog System**: Full-featured blog with categories, tags, CKEditor 5 rich text editing, and seamless navigation
- **Project Portfolio**: Showcase projects with images, videos, and PDF documents
- **Resume Section**: Display your experience, education, and skills
- **Contact Form**: Integrated email contact form with SMTP support
- **GitHub Integration**: Automatically fetches and displays your GitHub repositories with language colors
- **Admin Panel**: Django admin interface for easy content management
- **Feature Flags**: Toggle navigation elements (like Projects link) via admin panel
- **Production Ready**: Includes security best practices and HTTPS support
- **Dockerized**: Complete Docker setup for development and production

## Quick Start (Docker)

The easiest way to run this project is using Docker. All dependencies, migrations, and static files are handled automatically.

### Prerequisites

- **Docker** and **Docker Compose**

### Local Development

1. **Clone the repository**:

   ```bash
   git clone https://github.com/karlokr/djangfolio
   cd djangfolio
   ```

2. **Create environment file**:

   ```bash
   cp .env.example .env
   ```
   The default `.env` settings work for local development. Edit if needed.

2. **Install npm packages**:

   ```bash
   npm install
   ```

4. **Start the application**:

   ```bash
   docker compose up --build
   ```

   That's it! The container automatically:
   - Installs all Python and npm dependencies
   - Runs database migrations
   - Collects static files
   - Starts the development server

5. **Access the site**:
   - Main site: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

6. **Create admin user** (first time only):

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
   Follow the prompts to create your admin account.

### Useful Docker Commands

```bash
# View logs
docker compose logs -f web

# Stop the container
docker compose down

# Rebuild after changes
docker compose up --build

# Access Django shell
docker compose exec web python manage.py shell

# Run Django commands
docker compose exec web python manage.py <command>
```

**Note**:

- The entire project directory is mounted into the container, so code changes are reflected immediately
- The database (`db.sqlite3`) persists in your project directory
- The development server auto-reloads when you modify Python files
- Static files are served by Django's development server in development mode
- WhiteNoise handles static files in production for better performance


## SPA-Like Navigation with HTMX

The site uses HTMX to provide a Single Page Application (SPA) experience while keeping the simplicity of server-rendered templates.

### How It Works

- The **navbar stays fixed** at the top of the page and is never reloaded
- Only the **main content area** (`#main-content`) updates when navigating between pages
- All navigation links use HTMX attributes (`hx-get`, `hx-target`, `hx-swap`, `hx-push-url`)
- The browser URL and history update properly, so bookmarks and back/forward buttons work
- Page transitions are instant with no flash of white/loading

### Technical Implementation

```html
<!-- Example navigation link -->
<a href="{% url 'blog:blog_list' %}"
   hx-get="{% url 'blog:blog_list' %}"
   hx-target="#main-content"
   hx-swap="innerHTML"
   hx-push-url="true">Blog</a>
```

- **`hx-get`**: Fetches the page content via AJAX
- **`hx-target="#main-content"`**: Only replaces the content area, not the whole page
- **`hx-swap="innerHTML"`**: Replaces the inner HTML of the target
- **`hx-push-url="true"`**: Updates the browser URL for proper history

### Partial Templates

Each view returns either a full page or a partial template based on the request type:

```python
# In views.py
template = 'blog/blog_list_partial.html' if request.htmx else 'blog/blog_list.html'
return render(request, template, context)
```

- **Full templates** (e.g., `blog_list.html`): Include the base layout with navbar, used for direct URL access
- **Partial templates** (e.g., `blog_list_partial.html`): Only the content, used for HTMX navigation


## Blog System

The blog system provides a full-featured blogging platform integrated with the portfolio site.

### Blog Features

- **Rich Text Editing**: CKEditor 5 integration for creating beautiful blog posts with images, code blocks, and formatting
- **Image Alignment**: Support for left, center, and right image alignment in posts
- **Categories & Tags**: Organize posts with categories and tags, sortable by post count in sidebar
- **Multi-Filter Support**: Filter posts by multiple categories or tags simultaneously (OR logic)
- **Related Posts**: Automatically displays up to 3 related posts based on shared categories
- **About the Author**: Sidebar section showing author profile, bio from resume, and social links
- **Author Attribution**: Default author pulled from Site Configuration, customizable per post
- **Featured Images**: Support for post thumbnails with optional captions
- **Pagination**: Smart pagination with consistent 5-page range display (simplified on mobile)
- **Social Sharing**: Share buttons for X/Twitter, Facebook, LinkedIn, Reddit, and Email
- **Responsive Design**: Mobile-optimized layout with inline share buttons on narrow screens

### Managing Blog Posts

1. Go to <http://localhost:8000/admin>
2. Click on **"Blog Posts"** under the Blog section
3. Click **"Add Blog Post"** to create a new post
4. Fill in the fields:
   - `title`: Post title (slug is auto-generated)
   - `content`: Rich text content using CKEditor 5
   - `excerpt`: Short summary for list views
   - `featured_image`: Optional header image
   - `featured_image_caption`: Optional caption for the featured image
   - `categories`: Select one or more categories
   - `tags`: Select one or more tags
   - `published`: Check to make the post visible
   - `author`: Defaults to site config full name
5. Click **Save**

### Managing Categories & Tags

- Categories and tags are managed separately in the admin panel
- Posts can be filtered by clicking on category/tag badges in the blog list
- Multiple filters can be applied (uses OR logic—shows posts matching any selected filter)
- Both are sorted by post count in the sidebar
- Remove individual filters by clicking the X on filter badges


## Site Configuration

The site uses a database-backed configuration system accessible through the Django admin panel.

### Configuring Your Site

1. Go to <http://localhost:8000/admin>
2. Login with your admin credentials
3. Click on **"Site Configurations"**
4. Edit the configuration entry
5. Update your personal information:
   - `full_name`: Your full name displayed on the site (also used as default blog author)
   - `contact_email`: Email where contact form messages are sent
   - `display_email`: Email address shown publicly on the site
   - `github_username`: Your GitHub username (for API integration)
   - `github_url`: Full URL to your GitHub profile
   - `linkedin_username`: Your LinkedIn username
   - `linkedin_url`: Full URL to your LinkedIn profile
   - `copyright_text`: Copyright text in the footer
   - `profile_image`: Upload your profile photo (recommended: 400x400px or larger, square)
   - `profile_image_alt_text`: Alt text for accessibility
   - `favicon`: Upload a site favicon (recommended: 32x32px or 64x64px)

6. Click **Save**

### Feature Flags

The site includes feature flags to toggle certain elements:

- **`show_projects_link`**: Show/hide the Projects link in the navigation bar (default: enabled)

Access feature flags in the Site Configuration admin panel.

## Local Development (Without Docker)

If you prefer to run the project without Docker:

### Prerequisites

- Python 3.12+ (or 3.8-3.12 for Django 4.2 compatibility)
- Node.js and npm

### Setup

1. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node dependencies**:

   ```bash
   npm install
   ```

4. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Collect static files**:

   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Create superuser**:

   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**:

   ```bash
   python manage.py runserver
   ```

8. **Access the site**:
   - Main site: <http://localhost:8000>
   - Admin panel: <http://localhost:8000/admin>

## Email Configuration

The contact form supports SMTP email sending. Configure these in your `.env` file:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@example.com
CONTACT_EMAIL=contact@example.com
```

**For Gmail**:

1. Enable 2-factor authentication
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password in `EMAIL_HOST_PASSWORD`

**For Development**:

- Use `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` to print emails to console instead of sending them

## Production Deployment

### Using Pre-built Docker Image

The portfolio site is available on Docker Hub:

```bash
# Pull the latest version
docker pull karlokr94/djangfolio:latest

# Or pull a specific version
docker pull karlokr94/djangfolio:v1.0.1
```

### Production Docker Compose

Create a `docker-compose.yml` for production:

```yaml
services:
  portfolio:
    image: karlokr94/djangfolio:latest
    container_name: djangfolio
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

Create a `.env` file:

```bash
# Django Settings
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# CSRF Protection (REQUIRED for HTTPS)
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
CONTACT_EMAIL=contact@yourdomain.com
```

### Important Production Settings

1. **SECRET_KEY**: Generate a new one for production

   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **ALLOWED_HOSTS**: Comma-separated list of domains Django will accept

   ```bash
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

3. **CSRF_TRUSTED_ORIGINS**: **Required for HTTPS** - Include the protocol

   ```bash
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **Database and Media**: Mount volumes to persist data

   ```yaml
   volumes:
     - ./db:/app/db          # SQLite database
     - ./media:/app/media    # Uploaded files
   ```

### HTTPS Setup with Reverse Proxy

This application is designed to work behind a reverse proxy (Traefik, Nginx, Caddy, etc.) for HTTPS.

**Django Security Settings** (automatically enabled in production):

- `SECURE_PROXY_SSL_HEADER`: Trusts `X-Forwarded-Proto` header from proxy
- `CSRF_COOKIE_SECURE`: CSRF cookies only sent over HTTPS
- `SESSION_COOKIE_SECURE`: Session cookies only sent over HTTPS
- `SECURE_CONTENT_TYPE_NOSNIFF`: Prevents MIME sniffing
- `SECURE_BROWSER_XSS_FILTER`: Enables XSS filter

**Traefik Example** - Add these labels to your Docker service:

```yaml
services:
  portfolio:
    image: karlokr94/djangfolio:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.portfolio.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.portfolio.entrypoints=websecure"
      - "traefik.http.routers.portfolio.tls.certresolver=letsencrypt"
      # CRITICAL: Forward HTTPS headers to Django
      - "traefik.http.middlewares.portfolio-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.routers.portfolio.middlewares=portfolio-headers"
```

**Nginx Example**:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;  # CRITICAL for Django HTTPS
    }
}
```

### Production Checklist

- [ ] Generate new `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain(s)
- [ ] Configure `CSRF_TRUSTED_ORIGINS` with `https://` prefix
- [ ] Set up email SMTP credentials
- [ ] Configure reverse proxy with HTTPS
- [ ] Ensure proxy forwards `X-Forwarded-Proto: https` header
- [ ] Mount volumes for database and media files
- [ ] Set up regular database backups
- [ ] Test file uploads through admin panel
- [ ] Test contact form email delivery

## Troubleshooting

### CSRF Verification Failed

If you get "CSRF verification failed" errors when using the admin panel:

1. **Check CSRF_TRUSTED_ORIGINS**: Must include the protocol (`https://`)

   ```bash
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

2. **Verify reverse proxy**: Must forward `X-Forwarded-Proto: https` header

3. **Clear browser cookies**: Sometimes needed after configuration changes

### File Upload Fails (ERR_ACCESS_DENIED)

1. **Check reverse proxy upload limits**: Nginx/Traefik may have file size restrictions
2. **Verify CSRF_TRUSTED_ORIGINS**: Required for POST requests over HTTPS
3. **Check X-Forwarded-Proto header**: Proxy must forward this header to Django

### Admin Panel Returns 400/500 Error

1. **Check ALLOWED_HOSTS**: Must include all domains serving the site
2. **Verify CSRF_TRUSTED_ORIGINS**: Required for HTTPS deployments
3. **Clear CDN/proxy cache**: May be caching old error responses
4. **Check logs**: `docker logs <container-name>`

## Security Notes

- **Never commit `.env` file** to version control
- **Generate new SECRET_KEY** for production (don't use the default)
- **Set DEBUG=False** in production
- **Use strong admin passwords**
- **Keep dependencies updated**: `pip install -U -r requirements.txt`
- **Enable HTTPS** in production (use Let's Encrypt)
- **Configure ALLOWED_HOSTS** properly
- **Backup your database** regularly

## Project Structure

```text
djangfolio/
├── docker-compose.yml     # Docker Compose for local development
├── Dockerfile             # Production Docker image
├── docker-entrypoint.sh   # Container startup script
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies (Bootstrap, jQuery)
├── manage.py              # Django management script
├── db/                    # Database directory
│   └── db.sqlite3         # SQLite database (auto-created)
├── portfolio/             # Django project settings
│   ├── settings.py        # Main configuration (includes CKEditor 5 config)
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI application
├── home/                  # Home app (landing page, contact form)
│   ├── models.py          # SiteConfiguration model (includes feature flags)
│   ├── views.py           # Views with HTMX support
│   ├── templates/         # Templates (base_layout.html, navbar.html, partials)
│   └── static/            # Static files (CSS, JS, images)
├── blog/                  # Blog app
│   ├── models.py          # BlogPost, BlogCategory, BlogTag models
│   ├── views.py           # Blog list/detail views with HTMX support
│   ├── admin.py           # Rich admin interface
│   ├── templates/         # Full and partial templates
│   └── static/            # Blog-specific CSS
├── projects/              # Projects app (portfolio showcase)
├── resume/                # Resume app (experience, education)
└── media/                 # User-uploaded files (auto-created)
```

## Technologies Used

- **Backend**: Django 4.2.16, Python 3.12
- **Database**: SQLite (development), compatible with PostgreSQL (production)
- **Frontend**: Bootstrap 4.5.2, jQuery 3.5.1, Font Awesome 6.5.1
- **SPA Navigation**: HTMX 1.9.10 with django-htmx middleware
- **Rich Text Editor**: CKEditor 5 (django-ckeditor-5)
- **Static Files**: WhiteNoise (production)
- **WSGI Server**: Gunicorn (production)
- **Containerization**: Docker, Docker Compose

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the GPLv3.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Recent Updates**:

- Added full blog system with CKEditor 5 rich text editing
- Implemented SPA-like navigation with HTMX (navbar stays fixed, only content updates)
- Added "About the Author" section in blog posts with resume bio and social links
- Added social sharing buttons (X/Twitter, Facebook, LinkedIn, Reddit, Email)
- Added feature flags for toggling navigation elements (e.g., Projects link)
- Mobile-optimized blog with responsive pagination and inline share buttons
- Enhanced GitHub integration with language colors and improved styling
- Fixed HTTPS/CSRF issues for production deployments
- Added support for reverse proxy HTTPS headers
- Improved Docker setup with automatic initialization
