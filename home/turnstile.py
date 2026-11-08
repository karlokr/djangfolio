"""Cloudflare Turnstile check for the contact forms.

The widget on the page (rendered by home/js/scripts.js) adds a one-time token
to the form as ``cf-turnstile-response``. The server confirms it with
Cloudflare's siteverify API before sending the message. Turnstile is off when
``TURNSTILE_SECRET_KEY`` is unset (see settings).
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
TOKEN_FIELD = 'cf-turnstile-response'
# Must match the ``action`` the widget is rendered with in scripts.js.
ACTION = 'contact'
# Cloudflare's tokens are at most 2048 characters.
MAX_TOKEN_LENGTH = 2048
TIMEOUT_SECONDS = 10


def enabled():
    return bool(settings.TURNSTILE_SECRET_KEY)


def verify(token, remote_ip=''):
    """True if Cloudflare accepts ``token``. Fails closed on any error."""
    if not token or len(token) > MAX_TOKEN_LENGTH:
        return False
    fields = {'secret': settings.TURNSTILE_SECRET_KEY, 'response': token}
    if remote_ip:
        fields['remoteip'] = remote_ip
    request = urllib.request.Request(
        SITEVERIFY_URL,
        data=urllib.parse.urlencode(fields).encode(),
        headers={'User-Agent': 'djangfolio'},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        logger.error('Turnstile siteverify failed: %s', error)
        return False

    if not result.get('success'):
        logger.info('Turnstile rejected a token: %s', result.get('error-codes'))
        return False
    # Cloudflare's dummy testing keys (handy for local development) answer
    # without an action, and flag it; real keys always return the action.
    testing_key = (result.get('metadata') or {}).get('result_with_testing_key')
    if result.get('action') != ACTION and not testing_key:
        logger.warning('Turnstile token was for action %r, not %r', result.get('action'), ACTION)
        return False
    return True
