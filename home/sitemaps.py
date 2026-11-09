"""sitemap.xml: the pages search engines should know about.

The home page, the blog and every published post, and the project pages
(plus the projects list while the navbar links to it). Addresses are on
SITE_URL when it's set, else on the requesting host.
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import BlogPost
from home.models import SiteConfiguration
from projects.models import Project


class SiteUrlSitemap(Sitemap):
    """Builds its addresses on SITE_URL's scheme and host when it's set."""

    def get_protocol(self, protocol=None):
        return urlsplit(settings.SITE_URL).scheme if settings.SITE_URL else super().get_protocol(protocol)

    def get_domain(self, site=None):
        return urlsplit(settings.SITE_URL).netloc if settings.SITE_URL else super().get_domain(site)


class PagesSitemap(SiteUrlSitemap):
    def items(self):
        pages = ['home:home_page', 'blog:blog_list']
        if SiteConfiguration.get_solo().show_projects_link:
            pages.append('projects:projects_list')
        return pages

    def location(self, item):
        return reverse(item)


class BlogPostSitemap(SiteUrlSitemap):
    def items(self):
        return BlogPost.objects.filter(published=True).order_by('-created_date')

    def location(self, post):
        return reverse('blog:blog_detail', args=[post.slug])

    def lastmod(self, post):
        return post.updated_date


class ProjectSitemap(SiteUrlSitemap):
    def items(self):
        return Project.objects.order_by('-pub_date')


SITEMAPS = {
    'pages': PagesSitemap,
    'blog': BlogPostSitemap,
    'projects': ProjectSitemap,
}
