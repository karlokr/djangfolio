"""Responsive image helpers.

``{% image_srcset field "120 240 360" %}`` returns a ``srcset`` value built
from resized copies of an uploaded image, so small spots (like the 120px blog
author avatar) don't download and shrink the full-size original.

Copies are made on first use with Pillow and saved next to the media files
under ``resized/``. A copy is remade whenever the original is newer, so
uploading a new profile photo refreshes them automatically.
"""
import logging
import os
from io import BytesIO

from django import template
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

register = template.Library()
logger = logging.getLogger(__name__)

# Saved formats keep their own type; anything else is written as JPEG.
_KEEP_FORMATS = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}


def _resized_name(name, width, ext):
    stem = os.path.splitext(name)[0]
    return f'resized/{stem}_{width}w.{ext}'


def _resized_url(field, width):
    """Return the URL of ``field`` resized to ``width`` px wide, or None."""
    storage = field.storage
    with Image.open(field.path) as source:
        original_width = source.width
        fmt = source.format if source.format in _KEEP_FORMATS else 'JPEG'
        if width >= original_width:
            return None
        name = _resized_name(field.name, width, _KEEP_FORMATS[fmt])
        if storage.exists(name) and (
            os.path.getmtime(storage.path(name)) >= os.path.getmtime(field.path)
        ):
            return storage.url(name)

        image = ImageOps.exif_transpose(source)
        height = round(image.height * width / image.width)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        if fmt == 'JPEG' and image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        buffer = BytesIO()
        options = {'quality': 85, 'optimize': True} if fmt in ('JPEG', 'WEBP') else {'optimize': True}
        image.save(buffer, fmt, **options)

    if storage.exists(name):
        storage.delete(name)
    storage.save(name, ContentFile(buffer.getvalue()))
    return storage.url(name)


@register.simple_tag
def image_srcset(field, widths):
    """Build a srcset from resized copies of ``field`` at the given widths.

    ``widths`` is a space-separated string of pixel widths. Widths at or above
    the original's width are skipped, and the original is always included as
    the largest candidate. On any error the original alone is returned, so a
    page never breaks over a missing or unreadable image.
    """
    if not field:
        return ''
    try:
        with Image.open(field.path) as source:
            original_width = ImageOps.exif_transpose(source).width
        entries = []
        for width in sorted({int(w) for w in str(widths).split()}):
            url = _resized_url(field, width)
            if url:
                entries.append(f'{url} {width}w')
        entries.append(f'{field.url} {original_width}w')
        return ', '.join(entries)
    except Exception:  # noqa: BLE001 - fall back to the original image
        logger.exception('Could not build srcset for %s', field.name)
        try:
            return field.url
        except Exception:  # noqa: BLE001
            return ''
