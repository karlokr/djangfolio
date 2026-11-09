"""
Context processors for the home app.
Makes site configuration available to all templates.
"""
from django.conf import settings
from .models import SiteConfiguration


def site_config(request):
    """
    Add site configuration to the context of all templates.
    This makes site_config available globally without needing to pass it in every view.
    
    Args:
        request: HttpRequest object (required by Django context processor interface)
    
    Returns:
        dict: Context dictionary with site_config and canonical_url
    """
    # The site's public origin: SITE_URL in production, else this request's.
    site_root = settings.SITE_URL or f'{request.scheme}://{request.get_host()}'
    # The canonical address keeps only the page number of a paginated list;
    # any other query (filters, tracking parameters) points to the plain page.
    canonical_url = site_root + request.path
    page = request.GET.get('page', '')
    if page.isdigit() and int(page) > 1:
        canonical_url += f'?page={int(page)}'

    return {
        'site_config': SiteConfiguration.get_solo(),
        'site_root': site_root,
        'canonical_url': canonical_url,
        # Empty when Turnstile is off; the contact forms then render without it.
        'turnstile_site_key': settings.TURNSTILE_SITE_KEY,
    }
