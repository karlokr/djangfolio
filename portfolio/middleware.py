"""Site-wide middleware."""
import secrets

from django.conf import settings


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
