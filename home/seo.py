"""Page titles and descriptions for search results and link previews.

Built from the admin's Site Configuration, the resume and the page's
content, so they suit any site. Views put them in the context as
``page_title`` and ``page_description``; templates use them for <title>,
the meta description and seo/social_meta.html.
"""
from django.conf import settings

from home.templatetags.custom_filters import seo_description

SEPARATOR = ' | '


def site_root(request):
    """The site's public origin: SITE_URL in production, else this request's."""
    return settings.SITE_URL or f'{request.scheme}://{request.get_host()}'


def page_title(*parts):
    """Join the non-empty parts: page_title('Blog', 'Jane Doe') -> 'Blog | Jane Doe'."""
    return SEPARATOR.join(part for part in parts if part)


def home_title(config, resume):
    """The SEO title from Site Configuration, else "<name> | <resume headline>"."""
    if config.seo_title:
        return config.seo_title
    name = resume.name if resume else config.full_name
    return page_title(name, resume.headline if resume else '')


def home_description(config, resume):
    """The meta description from Site Configuration, else the start of the about text."""
    about = resume.about_text if resume else ''
    return seo_description(config.meta_description or about or config.full_name)


def listing_description(intro, names, connector='on', limit=4):
    """'<intro> <connector> A, B, C and D.' for a list page, naming up to ``limit`` items."""
    names = [name for name in names if name][:limit]
    if not names:
        return seo_description(intro + '.')
    joined = names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
    return seo_description(f'{intro} {connector} {joined}.')


# Structured data (JSON-LD, https://schema.org): views put a list of these
# in the context as ``structured_data``; base_layout.html renders it.

def _profile_urls(config):
    """The configured profile URLs, minus the model's placeholder defaults."""
    urls = []
    for field in ('github_url', 'gitlab_url', 'x_url'):
        url = getattr(config, field)
        if url and url != config._meta.get_field(field).default:
            urls.append(url)
    return urls


def person(request, config, resume, description=''):
    """The site's owner, with their job title and other profiles (sameAs)."""
    root = site_root(request)
    data = {
        '@type': 'Person',
        '@id': f'{root}/#person',
        'name': resume.name if resume else config.full_name,
        'url': f'{root}/',
    }
    if resume and resume.headline:
        data['jobTitle'] = resume.headline
    if resume and resume.location:
        data['homeLocation'] = {'@type': 'Place', 'name': resume.location}
    if description:
        data['description'] = description
    if config.profile_image:
        data['image'] = root + config.profile_image.url
    profiles = _profile_urls(config)
    if profiles:
        data['sameAs'] = profiles
    return data


def website(request, config):
    root = site_root(request)
    return {
        '@type': 'WebSite',
        '@id': f'{root}/#website',
        'name': config.full_name,
        'url': f'{root}/',
        'author': {'@id': f'{root}/#person'},
    }


def blog_posting(request, config, post, description):
    root = site_root(request)
    data = {
        '@type': 'BlogPosting',
        'headline': post.title[:110],
        'description': description,
        'datePublished': post.created_date.isoformat(),
        'dateModified': post.updated_date.isoformat(),
        'mainEntityOfPage': root + request.path,
        # The site's owner when they wrote it, else just the author's name.
        'author': ({'@id': f'{root}/#person'} if post.author == config.full_name
                   else {'@type': 'Person', 'name': post.author}),
    }
    if post.featured_image:
        data['image'] = [root + post.featured_image.url]
    return data


def breadcrumbs(request, *trail):
    """A BreadcrumbList from (name, path) pairs, starting at the home page."""
    root = site_root(request)
    return {
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': name, 'item': root + path}
            for i, (name, path) in enumerate(trail, start=1)
        ],
    }

