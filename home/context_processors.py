"""
Context processors for the home app.
Makes site configuration available to all templates.
"""
from .models import SiteConfiguration


def site_config(request):  # noqa: ARG001
    """
    Add site configuration to the context of all templates.
    This makes site_config available globally without needing to pass it in every view.
    
    Args:
        request: HttpRequest object (required by Django context processor interface)
    
    Returns:
        dict: Context dictionary with site_config
    """
    return {
        'site_config': SiteConfiguration.get_solo()
    }
