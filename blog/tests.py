from django.test import TestCase

from blog.models import BlogTag


class BlogListCrawlerTests(TestCase):
    """Filtered blog lists are endless for crawlers, so they're kept out."""

    def setUp(self):
        BlogTag.objects.get_or_create(slug='python', defaults={'name': 'Python'})

    def test_unfiltered_list_is_indexable(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('X-Robots-Tag', response)
        self.assertNotContains(response, 'name="robots"')

    def test_filtered_list_is_noindex_with_canonical(self):
        response = self.client.get('/blog/?tag=python&category=misc')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">')
        self.assertContains(response, '<link rel="canonical" href="http://testserver/blog/">')

    def test_filtered_partial_sends_header(self):
        response = self.client.get('/blog/?tag=python', HTTP_HX_REQUEST='true')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')

    def test_filter_links_are_nofollow(self):
        response = self.client.get('/blog/')
        self.assertContains(response, '<a rel="nofollow" href="/blog/?tag=python&"')
