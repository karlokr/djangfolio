import json
import urllib.error
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from home import github
from home.models import SiteConfiguration

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

GITHUB_REPOS = [
    {
        'name': 'repo-one', 'html_url': 'https://github.com/someone/repo-one',
        'description': 'First', 'language': 'Python',
        'stargazers_count': 3, 'forks_count': 1, 'private': False,
    },
    {
        'name': 'repo-two', 'html_url': 'https://github.com/someone/repo-two',
        'description': None, 'language': None,
        'stargazers_count': 0, 'forks_count': 0,
    },
]


def github_response(repos, etag='"v1"'):
    response = mock.MagicMock()
    response.status = 200
    response.headers = {'ETag': etag}
    response.read.return_value = json.dumps(repos).encode()
    response.__enter__.return_value = response
    return response


def http_error(code):
    return urllib.error.HTTPError('https://api.github.com', code, 'error', {}, None)


@override_settings(CACHES=LOCMEM, GITHUB_TOKEN='')
class GetReposTests(TestCase):
    def setUp(self):
        cache.clear()
        patcher = mock.patch('home.github.urllib.request.urlopen')
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)

    def test_first_call_fetches_and_keeps_only_shown_fields(self):
        self.urlopen.return_value = github_response(GITHUB_REPOS)
        repos = github.get_repos('someone')
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertEqual(repos[0], {
            'name': 'repo-one', 'html_url': 'https://github.com/someone/repo-one',
            'description': 'First', 'language': 'Python',
            'stargazers_count': 3, 'forks_count': 1,
        })
        self.assertEqual(repos[1]['description'], '')
        self.assertEqual(repos[1]['language'], '')

    def test_cached_list_is_served_without_calling_github(self):
        self.urlopen.return_value = github_response(GITHUB_REPOS)
        github.get_repos('someone')
        github.get_repos('someone')
        github.get_repos('someone')
        self.assertEqual(self.urlopen.call_count, 1)

    def test_refresh_sends_etag_and_reuses_list_on_304(self):
        self.urlopen.return_value = github_response(GITHUB_REPOS, etag='"abc"')
        first = github.get_repos('someone')
        cache.delete(github._keys('someone')[0])  # the hour is up
        self.urlopen.side_effect = http_error(304)
        second = github.get_repos('someone')
        request = self.urlopen.call_args[0][0]
        self.assertEqual(request.get_header('If-none-match'), '"abc"')
        self.assertEqual(second, first)

    def test_github_failure_serves_last_good_copy(self):
        self.urlopen.return_value = github_response(GITHUB_REPOS)
        first = github.get_repos('someone')
        cache.delete(github._keys('someone')[0])
        self.urlopen.side_effect = http_error(403)  # rate limited
        self.assertEqual(github.get_repos('someone'), first)
        # The failure backs off instead of retrying on every request.
        github.get_repos('someone')
        self.assertEqual(self.urlopen.call_count, 2)

    def test_failure_with_nothing_cached_backs_off_with_empty_list(self):
        self.urlopen.side_effect = http_error(403)  # rate limited
        self.assertEqual(github.get_repos('someone'), [])
        # Later requests within the back-off don't call GitHub again.
        self.assertEqual(github.get_repos('someone'), [])
        self.assertEqual(self.urlopen.call_count, 1)

    def test_concurrent_refresh_uses_last_good_copy(self):
        self.urlopen.return_value = github_response(GITHUB_REPOS)
        first = github.get_repos('someone')
        fresh_key, _last_good, lock_key = github._keys('someone')
        cache.delete(fresh_key)
        cache.add(lock_key, 1)  # another request is refreshing right now
        self.assertEqual(github.get_repos('someone'), first)
        self.assertEqual(self.urlopen.call_count, 1)

    @override_settings(GITHUB_TOKEN='secret-token')
    def test_token_is_sent_when_configured(self):
        self.urlopen.return_value = github_response(GITHUB_REPOS)
        github.get_repos('someone')
        request = self.urlopen.call_args[0][0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer secret-token')


@override_settings(CACHES=LOCMEM)
class GithubReposViewTests(TestCase):
    def setUp(self):
        cache.clear()
        config = SiteConfiguration.get_solo()
        config.github_username = 'someone'
        config.save()

    @mock.patch('home.views.get_repos', return_value=[{'name': 'repo-one'}])
    def test_returns_cached_repos(self, get_repos):
        response = self.client.get('/github-repos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'username': 'someone', 'repos': [{'name': 'repo-one'}]})
        self.assertIn('max-age=300', response['Cache-Control'])
        get_repos.assert_called_once_with('someone')

    @mock.patch('home.views.get_repos', return_value=None)
    def test_unavailable_returns_empty_list(self, _get_repos):
        response = self.client.get('/github-repos/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['repos'], [])

    def test_post_not_allowed(self):
        self.assertEqual(self.client.post('/github-repos/').status_code, 405)
