import json
import re
import urllib.error
import urllib.parse
from unittest import mock

from django.core import mail
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
        for url in ['/', '/blog/', '/blog/a-post/', '/projects/', self.project.get_absolute_url()]:
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

    def test_after_swap_handles_history_restores(self):
        from pathlib import Path
        from django.conf import settings

        source = (Path(settings.BASE_DIR) / 'home/templates/base_layout.html').read_text()
        # Back fires htmx:afterSwap with no detail.target; reading .id off it
        # threw and skipped the rest of the set-up (blog image pop-ups).
        unguarded = re.findall(r'(?<!event\.detail\.target && )event\.detail\.target\.id', source)
        self.assertEqual(unguarded, [])

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


def siteverify_response(result):
    response = mock.MagicMock()
    response.read.return_value = json.dumps(result).encode()
    response.__enter__.return_value = response
    return response


@override_settings(CACHES=LOCMEM, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   CONTACT_EMAIL='me@example.com', DEFAULT_FROM_EMAIL='site@example.com')
class ContactTurnstileTests(TestCase):
    """The contact form checks a Turnstile token with Cloudflare when configured."""

    FORM = {'name': 'Ann', 'email': 'ann@example.com', 'subject': 'Hi', 'message': 'Hello'}

    def setUp(self):
        cache.clear()

    def post(self, **extra):
        return self.client.post('/send-email/', {**self.FORM, **extra}, HTTP_CF_CONNECTING_IP='203.0.113.7')

    def test_off_without_keys(self):
        with mock.patch('home.turnstile.urllib.request.urlopen') as urlopen:
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        urlopen.assert_not_called()

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_missing_token_is_rejected_without_calling_cloudflare(self):
        with mock.patch('home.turnstile.urllib.request.urlopen') as urlopen:
            response = self.post()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)
        urlopen.assert_not_called()

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_valid_token_sends_message(self):
        result = {'success': True, 'action': 'contact', 'hostname': 'example.com'}
        with mock.patch('home.turnstile.urllib.request.urlopen',
                        return_value=siteverify_response(result)) as urlopen:
            response = self.post(**{'cf-turnstile-response': 'tok'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        sent = urlopen.call_args.args[0]
        self.assertEqual(sent.full_url, 'https://challenges.cloudflare.com/turnstile/v0/siteverify')
        self.assertEqual(urllib.parse.parse_qs(sent.data.decode()),
                         {'secret': ['secret'], 'response': ['tok'], 'remoteip': ['203.0.113.7']})

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_rejected_tokens(self):
        for name, outcome in [
            ('cloudflare says no', siteverify_response({'success': False, 'error-codes': ['invalid-input-response']})),
            ('token for another action', siteverify_response({'success': True, 'action': 'login'})),
            ('cloudflare unreachable', urllib.error.URLError('down')),
        ]:
            with self.subTest(name), mock.patch('home.turnstile.urllib.request.urlopen', side_effect=[outcome]):
                response = self.post(**{'cf-turnstile-response': 'tok'})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_cloudflare_testing_keys_pass_without_an_action(self):
        # What siteverify returns for Cloudflare's dummy testing secret keys.
        result = {'success': True, 'error-codes': [], 'hostname': 'example.com',
                  'metadata': {'result_with_testing_key': True}}
        with mock.patch('home.turnstile.urllib.request.urlopen', return_value=siteverify_response(result)):
            response = self.post(**{'cf-turnstile-response': 'XXXX.DUMMY.TOKEN.XXXX'})
        self.assertEqual(response.status_code, 200)

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_oversized_token_is_rejected_without_calling_cloudflare(self):
        with mock.patch('home.turnstile.urllib.request.urlopen') as urlopen:
            response = self.post(**{'cf-turnstile-response': 'x' * 2049})
        self.assertEqual(response.status_code, 403)
        urlopen.assert_not_called()

    def test_widget_slots_only_render_with_a_site_key(self):
        self.assertNotContains(self.client.get('/'), 'turnstile-slot')
        with self.settings(TURNSTILE_SITE_KEY='site-key-123', TURNSTILE_SECRET_KEY='secret'):
            self.assertContains(self.client.get('/'),
                                '<div class="turnstile-slot" data-sitekey="site-key-123"></div>', count=2)


class NotFoundCachingTests(TestCase):
    """A 404 must never be cached (Cloudflare kept one for hours after a deploy)."""

    def test_404s_are_not_cacheable(self):
        for url in ['/static/home/css/style.000000000000.css', '/no-such-page/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertIn('no-store', response['Cache-Control'])
                self.assertIn('max-age=0', response['Cache-Control'])

    def test_other_responses_keep_their_caching(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('no-store', response.get('Cache-Control', ''))


class SeoTests(TestCase):
    """One host, canonical links, titles, descriptions and link-preview tags."""

    HOSTS = ['example.com', 'www.example.com', 'testserver']

    def setUp(self):
        from blog.models import BlogPost
        from resume.models import Resume

        self.resume = Resume.objects.create(
            name='Jane Doe', headline='Data Engineer', location='Earth',
            about_text='I build pipelines. ' * 30)
        BlogPost.objects.create(title='A Post', slug='a-post', excerpt='Short excerpt.',
                                content='Body', published=True)
        config = SiteConfiguration.get_solo()
        config.full_name = 'Jane Doe'
        config.save()

    def head(self, response):
        html = response.content.decode()
        return html[:html.index('</head>')]

    @override_settings(SITE_URL='https://example.com', ALLOWED_HOSTS=HOSTS)
    def test_other_hosts_redirect_to_site_url(self):
        response = self.client.get('/blog/?page=2', HTTP_HOST='www.example.com')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://example.com/blog/?page=2')
        self.assertEqual(self.client.get('/blog/', HTTP_HOST='example.com').status_code, 200)

    @override_settings(SITE_URL='', ALLOWED_HOSTS=HOSTS)
    def test_no_redirect_without_site_url(self):
        self.assertEqual(self.client.get('/', HTTP_HOST='www.example.com').status_code, 200)

    @override_settings(SITE_URL='https://example.com', ALLOWED_HOSTS=HOSTS)
    def test_canonical_links(self):
        for url, canonical in [
            ('/', 'https://example.com/'),
            ('/blog/a-post/', 'https://example.com/blog/a-post/'),
            ('/blog/?page=2&utm_source=x', 'https://example.com/blog/?page=2'),
            ('/blog/?page=1', 'https://example.com/blog/'),
            ('/blog/?tag=python&page=2', 'https://example.com/blog/'),
            ('/projects/', 'https://example.com/projects/'),
        ]:
            with self.subTest(url=url):
                head = self.head(self.client.get(url, HTTP_HOST='example.com'))
                self.assertEqual(re.findall(r'<link rel="canonical" href="([^"]+)">', head), [canonical])

    def test_titles(self):
        for url, title in [
            ('/', 'Jane Doe | Data Engineer'),
            ('/blog/', 'Blog | Jane Doe'),
            ('/blog/a-post/', 'A Post | Jane Doe'),
            ('/projects/', 'Projects | Jane Doe'),
        ]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), f'<title>{title}</title>')

    def test_seo_title_overrides_the_home_title(self):
        config = SiteConfiguration.get_solo()
        config.seo_title = 'Jane Doe, pipelines and data'
        config.save()
        self.assertContains(self.client.get('/'), '<title>Jane Doe, pipelines and data</title>')

    def test_home_description(self):
        head = self.head(self.client.get('/'))
        description = re.search(r'<meta name="description" content="([^"]*)">', head).group(1)
        self.assertLessEqual(len(description), 160)
        self.assertTrue(description.endswith('pipelines.…') or description.endswith('…'))
        self.assertTrue(description.startswith('I build pipelines.'))
        config = SiteConfiguration.get_solo()
        config.meta_description = 'Data engineer building pipelines.'
        config.save()
        self.assertContains(self.client.get('/'), '<meta name="description" content="Data engineer building pipelines.">')

    @override_settings(SITE_URL='https://example.com', ALLOWED_HOSTS=HOSTS)
    def test_link_preview_tags(self):
        head = self.head(self.client.get('/', HTTP_HOST='example.com'))
        self.assertIn('<meta property="og:url" content="https://example.com/">', head)
        self.assertIn('<meta property="og:title" content="Jane Doe | Data Engineer">', head)
        self.assertIn('<meta name="twitter:card" content="summary">', head)
        self.assertNotIn('property="twitter:', head)
        post = self.head(self.client.get('/blog/a-post/', HTTP_HOST='example.com'))
        self.assertIn('<meta property="og:type" content="article">', post)
        self.assertIn('<meta property="og:title" content="A Post">', post)
        self.assertIn('property="article:modified_time"', post)

    def test_seo_description_filter(self):
        from home.templatetags.custom_filters import seo_description

        self.assertEqual(seo_description('<p>Short   text.</p>'), 'Short text.')
        long = seo_description('word ' * 60)
        self.assertLessEqual(len(long), 160)
        self.assertTrue(long.endswith('word…'))

    def test_listing_description(self):
        from home import seo

        self.assertEqual(seo.listing_description('Articles by Jane', ['A', 'B', 'C']),
                         'Articles by Jane on A, B and C.')
        self.assertEqual(seo.listing_description('Articles by Jane', []), 'Articles by Jane.')
