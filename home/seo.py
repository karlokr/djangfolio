"""Page titles and descriptions for search results and link previews.

Built from the admin's Site Configuration, the resume and the page's
content, so they suit any site. Views put them in the context as
``page_title`` and ``page_description``; templates use them for <title>,
the meta description and seo/social_meta.html.
"""
from home.templatetags.custom_filters import seo_description

SEPARATOR = ' | '


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
