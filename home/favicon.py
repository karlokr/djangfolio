"""Square icons made from the favicon uploaded in Site Configuration.

Browsers, search engines and phones look for icons at fixed addresses and
sizes, and search engines want them square. These views serve the uploaded
favicon at each of those: padded to a square (never stretched), resized, and
cached until the favicon is replaced.
"""
import os
from io import BytesIO

from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_safe
from PIL import Image

from home.models import SiteConfiguration

ICO_SIZES = [(16, 16), (32, 32), (48, 48)]
CACHE_SECONDS = 24 * 60 * 60


def _square(image, size, background=None):
    """``image`` centred on a transparent (or ``background``) square, resized to ``size``."""
    image = image.convert('RGBA')
    side = max(image.size)
    canvas = Image.new('RGBA', (side, side), background or (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2), image)
    return canvas.resize((size, size), Image.LANCZOS)


def _icon(kind, render):
    """The icon bytes for ``kind``, rendered once per uploaded favicon."""
    favicon = SiteConfiguration.get_solo().favicon
    if not favicon:
        raise Http404('No favicon configured')
    try:
        stamp = os.path.getmtime(favicon.path)
    except (OSError, NotImplementedError):
        stamp = ''
    key = f'favicon:{kind}:{favicon.name}:{stamp}'
    data = cache.get(key)
    if data is None:
        with favicon.open('rb') as f, Image.open(f) as source:
            buffer = BytesIO()
            render(source, buffer)
            data = buffer.getvalue()
        cache.set(key, data, timeout=None)
    return data


def _response(data, content_type):
    response = HttpResponse(data, content_type=content_type)
    response['Cache-Control'] = f'public, max-age={CACHE_SECONDS}'
    return response


@require_safe
def favicon_ico(request):
    """/favicon.ico, where browsers and crawlers look without being told."""
    def render(source, buffer):
        _square(source, 48).save(buffer, format='ICO', sizes=ICO_SIZES)
    return _response(_icon('ico', render), 'image/x-icon')


@require_safe
def favicon_png(request):
    """192px PNG: the size browsers and search engines prefer to scale down from."""
    def render(source, buffer):
        _square(source, 192).save(buffer, format='PNG', optimize=True)
    return _response(_icon('png192', render), 'image/png')


@require_safe
def apple_touch_icon(request):
    """180px on white: iOS shows transparent areas of a home-screen icon as black."""
    def render(source, buffer):
        _square(source, 180, background=(255, 255, 255, 255)).convert('RGB').save(buffer, format='PNG', optimize=True)
    return _response(_icon('apple180', render), 'image/png')
