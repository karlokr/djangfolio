"""Site-wide middleware."""
import secrets

from django.conf import settings
from django.utils.cache import add_never_cache_headers


class NeverCacheNotFoundMiddleware:
    """Mark 404 responses as never cacheable.

    During a deploy, a page from the new container can ask for a static file
    (``style.<new hash>.css``) that the old container, still answering some
    requests, doesn't have. Cloudflare cached that 404 and told browsers to
    keep it for 4 hours, so the site stayed unstyled after the deploy
    finished. Uncacheable, a 404 only affects the one request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            add_never_cache_headers(response)
        return response


class ContentSecurityPolicyMiddleware:
    """Send a Content-Security-Policy header with a per-request script nonce.

    Each request gets a fresh random nonce, available to templates as
    ``{{ request.csp_nonce }}``. Inline ``<script>`` tags must carry it
    (``<script nonce="{{ request.csp_nonce }}">``) to run; any script injected
    into the page without it is blocked. The policy itself lives in
    ``settings.CONTENT_SECURITY_POLICY``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)

        header = (
            'Content-Security-Policy-Report-Only'
            if getattr(settings, 'CSP_REPORT_ONLY', False)
            else 'Content-Security-Policy'
        )
        if header not in response:
            response[header] = self.build_policy(request.csp_nonce)
        return response

    @staticmethod
    def build_policy(nonce):
        directives = []
        for name, sources in settings.CONTENT_SECURITY_POLICY.items():
            values = ' '.join(source.format(nonce=nonce) for source in sources)
            directives.append(f'{name} {values}'.strip())
        return '; '.join(directives)
