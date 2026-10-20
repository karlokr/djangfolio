"""portfolio URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from functools import wraps

from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.static import serve
from markdownx.views import ImageUploadView, MarkdownifyView


def staff_only(view):
    """Allow only logged-in staff; everyone else gets 403 Forbidden."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # The markdown editor's image upload and preview endpoints are only used
    # from the admin, so they're limited to staff (markdownx leaves them open).
    path('markdownx/upload/', staff_only(ImageUploadView.as_view()), name='markdownx_upload'),
    path('markdownx/markdownify/', staff_only(MarkdownifyView.as_view()), name='markdownx_markdownify'),
    path('blog/', include('blog.urls')),
    path('projects/', include('projects.urls')),
    path('', include('home.urls')),
    # Serve media files manually for production
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
