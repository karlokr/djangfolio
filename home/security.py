"""Small security helpers shared across the site."""
from django.core.cache import cache


def client_ip(request):
    """Return the visitor's IP address.

    In production the site sits behind Cloudflare and Traefik, so
    REMOTE_ADDR is the proxy's address. Cloudflare's CF-Connecting-IP header
    holds the real visitor address; X-Forwarded-For is the fallback when
    Cloudflare isn't in front (for example a direct Traefik request).

    These headers can be forged by anyone who reaches the app without going
    through Cloudflare, so keep port 8000 closed to the internet.
    """
    meta = request.META
    ip = meta.get('HTTP_CF_CONNECTING_IP', '').strip()
    if not ip:
        forwarded = meta.get('HTTP_X_FORWARDED_FOR', '')
        ip = forwarded.split(',')[0].strip()
    return ip or meta.get('REMOTE_ADDR', '')


def rate_limited(key, limit, window_seconds):
    """Count one hit for ``key``; return True once it exceeds ``limit``.

    The count resets ``window_seconds`` after the first hit.
    """
    cache_key = f'ratelimit:{key}'
    # add() only sets the key if it doesn't exist, which starts the window.
    cache.add(cache_key, 0, timeout=window_seconds)
    try:
        hits = cache.incr(cache_key)
    except ValueError:
        # The key expired between add() and incr(); start a new window.
        cache.set(cache_key, 1, timeout=window_seconds)
        hits = 1
    return hits > limit
