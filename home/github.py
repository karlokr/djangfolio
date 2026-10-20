"""Server-side, cached access to the GitHub repos shown on the home page.

Visitors' browsers used to call the GitHub API themselves (about 10 requests
per page view), which quickly hit GitHub's anonymous limit of 60 requests an
hour per IP address and showed 403 errors. Now the server fetches the repo
list at most once an hour, caches it, and the page reads it from this site.

- Refreshes send the previous response's ETag; GitHub answers "304 Not
  Modified" when nothing changed, and those don't count against the limit.
- If GitHub is unreachable or rate-limited, the last good copy keeps being
  served, so the section never goes blank once it has loaded once.
- Optional: set GITHUB_TOKEN (a token with no scopes is enough) to raise the
  limit from 60 to 5,000 requests an hour. Not needed at one call an hour.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

API_URL = 'https://api.github.com/users/{username}/repos?sort=pushed&per_page={count}'
REPO_COUNT = 9
FRESH_SECONDS = 60 * 60  # how long a fetched list is used before refreshing
RETRY_SECONDS = 5 * 60   # after a failed refresh, keep the old copy this long
TIMEOUT_SECONDS = 5


def _keys(username):
    base = f'github:repos:{username.lower()}'
    return f'{base}:fresh', f'{base}:last-good', f'{base}:lock'


def _summarize(repo):
    """Keep only the fields the page shows."""
    return {
        'name': repo.get('name') or '',
        'html_url': repo.get('html_url') or '',
        'description': repo.get('description') or '',
        'language': repo.get('language') or '',
        'stargazers_count': repo.get('stargazers_count') or 0,
        'forks_count': repo.get('forks_count') or 0,
    }


def _fetch(username, etag):
    """Return (status, etag, repos); repos is None for 304 Not Modified."""
    request = urllib.request.Request(
        API_URL.format(username=username, count=REPO_COUNT),
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'djangfolio',
            'X-GitHub-Api-Version': '2022-11-28',
        },
    )
    if etag:
        request.add_header('If-None-Match', etag)
    token = getattr(settings, 'GITHUB_TOKEN', '')
    if token:
        request.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode('utf-8'))
            return response.status, response.headers.get('ETag'), [_summarize(r) for r in data]
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return 304, etag, None
        raise


def get_repos(username):
    """Return the repo list for ``username``.

    Returns [] if GitHub has never answered successfully (and backs off for a
    few minutes before trying again), or None while the very first fetch is
    in progress in another request.
    """
    if not username:
        return None
    fresh_key, last_good_key, lock_key = _keys(username)

    repos = cache.get(fresh_key)
    if repos is not None:
        return repos

    last_good = cache.get(last_good_key)  # {'etag': ..., 'repos': [...]}
    # Only one request refreshes at a time; the rest use the last good copy.
    if not cache.add(lock_key, 1, timeout=TIMEOUT_SECONDS * 6):
        return last_good['repos'] if last_good else None

    try:
        status, etag, fetched = _fetch(username, last_good['etag'] if last_good else None)
        if fetched is None:  # 304: nothing changed since the last fetch
            fetched = last_good['repos']
        cache.set(fresh_key, fetched, timeout=FRESH_SECONDS)
        cache.set(last_good_key, {'etag': etag, 'repos': fetched}, timeout=None)
        return fetched
    except (urllib.error.URLError, OSError, ValueError) as error:
        logger.warning('Could not refresh GitHub repos for %s: %s', username, error)
        # Don't retry on every request while GitHub is failing: serve the last
        # good copy (or an empty list if there has never been one) for a while.
        repos = last_good['repos'] if last_good else []
        cache.set(fresh_key, repos, timeout=RETRY_SECONDS)
        return repos
    finally:
        cache.delete(lock_key)
