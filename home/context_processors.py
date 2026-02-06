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
    # Build canonical URL - use SITE_URL if set, otherwise use request
    if settings.SITE_URL:
        canonical_url = settings.SITE_URL.rstrip('/') + request.path
    else:
        canonical_url = request.build_absolute_uri()
    
    return {
        'site_config': SiteConfiguration.get_solo(),
        'canonical_url': canonical_url,
    }
