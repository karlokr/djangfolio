"""Responsive image helpers.

``{% image_srcset field "120 240 360" %}`` returns a ``srcset`` value built
from resized copies of an uploaded image, so a spot that shows an image small
(a 120px avatar, a 350px card) doesn't download the full-size original.
``add_srcset_to_media_images(html, sizes)`` does the same for ``<img>`` tags
inside rendered HTML, such as blog post bodies.

Copies are made on first use with Pillow and saved under ``resized/`` in the
media storage. A copy is remade whenever the original is newer, so replacing
an upload refreshes its copies automatically. Animated images are left as-is:
resizing would keep only their first frame.

Templates keep ``src`` pointing at the original, both as the fallback and
because the click-to-enlarge viewers read ``src`` to show the full image.
"""
import logging
import os
import re
import tempfile
from io import BytesIO

from django import template
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.utils.html import escape
from PIL import Image, ImageOps

register = template.Library()
logger = logging.getLogger(__name__)

# Saved formats keep their own type; anything else is written as JPEG.
_KEEP_FORMATS = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}

# Default widths, wide enough for 2x screens at every size the site uses.
DEFAULT_WIDTHS = (240, 360, 480, 720, 960, 1440)


def _resized_name(name, width, ext):
    stem = os.path.splitext(name)[0]
    return f'resized/{stem}_{width}w.{ext}'


def _source_info(path):
    """Return (width, format, animated) for the image at ``path``.

    Reads only the file header (no decoding) and caches the answer per file
    version, so pages don't reopen every image on every request.
    """
    cache_key = f'imginfo:{path}:{os.path.getmtime(path)}'
    info = cache.get(cache_key)
    if info is None:
        with Image.open(path) as source:
            width, height = source.size
            # EXIF orientations 5-8 are rotated 90 degrees: displayed width is
            # the stored height.
            if source.getexif().get(0x0112) in (5, 6, 7, 8):
                width = height
            info = (width, source.format, getattr(source, 'is_animated', False))
        cache.set(cache_key, info, timeout=None)
    return info


def _make_copy(storage, name, path, width, fmt):
    """Create (or refresh) the resized copy of ``name``; return its URL."""
    fmt = fmt if fmt in _KEEP_FORMATS else 'JPEG'
    copy_name = _resized_name(name, width, _KEEP_FORMATS[fmt])
    if storage.exists(copy_name) and (
        os.path.getmtime(storage.path(copy_name)) >= os.path.getmtime(path)
    ):
        return storage.url(copy_name)

    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        height = round(image.height * width / image.width)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        if fmt == 'JPEG' and image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        buffer = BytesIO()
        options = {'quality': 85, 'optimize': True} if fmt in ('JPEG', 'WEBP') else {'optimize': True}
        image.save(buffer, fmt, **options)

    # Write to a temporary file and rename it into place. The rename is atomic,
    # so when several app replicas share the media folder and make the same
    # copy at once, the last one simply wins; storage.save() would instead
    # save a duplicate under a random name.
    path_out = storage.path(copy_name)
    folder = os.path.dirname(path_out)
    os.makedirs(folder, exist_ok=True)
    # mkstemp gives a unique name even across threads and containers, whose
    # process IDs can coincide.
    fd, tmp = tempfile.mkstemp(dir=folder, suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(buffer.getvalue())
        os.chmod(tmp, 0o644)  # mkstemp creates the file owner-only
        os.replace(tmp, path_out)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return storage.url(copy_name)


def srcset_for(name, widths=DEFAULT_WIDTHS, storage=default_storage):
    """Build a srcset for the stored file ``name``, or '' if not possible.

    Widths at or above the original's width are skipped, and the original is
    always the largest candidate. Returns '' (so templates just use ``src``)
    for animated images and on any error, so a page never breaks over an
    image.
    """
    try:
        path = storage.path(name)
        width, fmt, animated = _source_info(path)
        if animated:
            return ''
        entries = [
            f'{_make_copy(storage, name, path, w, fmt)} {w}w'
            for w in sorted(set(widths)) if w < width
        ]
        entries.append(f'{storage.url(name)} {width}w')
        return ', '.join(entries)
    except Exception:  # noqa: BLE001 - fall back to plain src
        logger.exception('Could not build srcset for %s', name)
        return ''


@register.simple_tag
def image_srcset(field, widths=''):
    """srcset for an ImageField/FieldFile; ``widths`` is space-separated px."""
    if not field:
        return ''
    chosen = [int(w) for w in str(widths).split()] or DEFAULT_WIDTHS
    return srcset_for(field.name, chosen, storage=field.storage)


_MEDIA_IMG = re.compile(r'<img\b([^>]*?)\bsrc="([^"]+)"([^>]*)>', re.IGNORECASE)


def add_srcset_to_media_images(html, sizes):
    """Add srcset/sizes to ``<img>`` tags in ``html`` that point at uploads.

    Only images under MEDIA_URL that don't already have a srcset are changed.
    """
    media_url = settings.MEDIA_URL

    def replace(match):
        before, src, after = match.groups()
        if 'srcset=' in before + after or not src.startswith(media_url):
            return match.group(0)
        name = src[len(media_url):]
        if name.startswith('resized/'):
            return match.group(0)
        srcset = srcset_for(name)
        if not srcset:
            return match.group(0)
        return (
            f'<img{before}src="{src}" srcset="{escape(srcset)}" '
            f'sizes="{escape(sizes)}"{after}>'
        )

    return _MEDIA_IMG.sub(replace, html)
