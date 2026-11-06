import json
import re
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


class RobotsTxtTests(TestCase):
    def test_disallows_blog_filters(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, 'Disallow: /blog/?*tag=')
        self.assertContains(response, 'Disallow: /blog/?*category=')


class HtmxTabTitleTests(TestCase):
    """htmx navigation must leave the tab with the same title as a full load."""

    def setUp(self):
        from blog.models import BlogPost
        from projects.models import Project
        from resume.models import Resume

        Resume.objects.create(name='Jane Doe', headline='Engineer', location='Earth', about_text='Hi')
        BlogPost.objects.create(title='A Post', slug='a-post', excerpt='x', content='Body', published=True)
        self.project = Project.objects.create(
            title='A Project', short_description='x', long_description='y', css_id='p')

    def titles(self, response):
        return re.findall(r'<title>(.*?)</title>', response.content.decode(), re.DOTALL)

    def test_partials_carry_the_full_page_title(self):
        for url in ['/', '/blog/', '/blog/a-post/', '/projects/', f'/projects/{self.project.pk}/']:
            with self.subTest(url=url):
                full = self.titles(self.client.get(url))
                partial = self.titles(self.client.get(url, HTTP_HX_REQUEST='true'))
                self.assertEqual(len(full), 1)
                self.assertTrue(full[0].strip())
                self.assertEqual(partial, full)


class GitLabLinkTests(TestCase):
    """The GitLab link sits between GitHub and X, and only once it's set."""

    def setUp(self):
        from blog.models import BlogPost
        from resume.models import Resume

        Resume.objects.create(name='Jane Doe', headline='Engineer', location='Earth', about_text='Hi')
        BlogPost.objects.create(title='A Post', slug='a-post', excerpt='x', content='Body', published=True)
        self.config = SiteConfiguration.get_solo()

    def test_blank_by_default_and_hidden(self):
        self.assertEqual(self.config.gitlab_url, '')
        for url in ['/', '/blog/a-post/']:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), 'fa-gitlab')

    def test_link_between_github_and_x(self):
        self.config.gitlab_url = 'https://gitlab.com/someone'
        self.config.save()
        for url in ['/', '/blog/a-post/']:
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertIn('href="https://gitlab.com/someone"', html)
                # The social-icon lists: GitHub, then GitLab, then X.
                block = html[html.rindex('aria-label="GitHub"'):]
                self.assertLess(block.index('aria-label="GitLab"'), block.index('aria-label="X (Twitter)"'))


class SiteScriptRerunTests(TestCase):
    """htmx re-runs base_layout's body script when Back restores <body>."""

    def test_global_listeners_are_added_once(self):
        from pathlib import Path
        from django.conf import settings

        source = (Path(settings.BASE_DIR) / 'home/templates/base_layout.html').read_text()
        # Listeners on document/body survive the restore: re-adding them would
        # stack duplicates, so top-level ones must go through listenOnce().
        self.assertIn('var siteScriptRerun', source)
        self.assertEqual(re.findall(r'^    document(?:\.body)?\.addEventListener\(', source, re.M), [])
        # The theme buttons are replaced by the restore, so clicks are delegated.
        self.assertNotIn("getElementById('theme-toggle", source)

    def test_social_buttons_have_tooltips(self):
        from blog.models import BlogPost
        from resume.models import Resume

        Resume.objects.create(name='Jane Doe', headline='Engineer', location='Earth', about_text='Hi')
        BlogPost.objects.create(title='A Post', slug='a-post', excerpt='x', content='Body', published=True)
        config = SiteConfiguration.get_solo()
        config.gitlab_url = 'https://gitlab.com/someone'
        config.save()
        for url in ['/', '/blog/a-post/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                for label in ['GitHub', 'GitLab', 'X', 'Email']:
                    self.assertContains(response, f'data-tooltip="{label}"', count=1)
