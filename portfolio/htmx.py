"""Helpers for serving full pages and htmx partials from the same URL.

Every page view returns a partial template to htmx and the full page to
everyone else, at the same URL. Two things keep those from getting mixed up:

* ``wants_partial`` sends the full page for htmx *history restores*. When the
  visitor goes Back and htmx no longer has the page in its history cache, it
  re-requests it and expects a whole page to put back in place.
* ``VaryOnHtmxMiddleware`` adds ``Vary: HX-Request`` to every response, so
  browser and proxy caches store the two versions separately. Without it, a
  Back navigation could be served the cached partial and render it as an
  unstyled page.
"""
from django.utils.cache import patch_vary_headers


def wants_partial(request):
    """True when the response should be the htmx partial template."""
    htmx = getattr(request, 'htmx', None)
    return bool(htmx) and not htmx.history_restore_request


class VaryOnHtmxMiddleware:
    """Add ``Vary: HX-Request`` so caches keep full pages and partials apart."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        patch_vary_headers(response, ('HX-Request',))
        return response
