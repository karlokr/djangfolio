from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

from home import favicon, views

app_name = 'home'
urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('favicon.ico', favicon.favicon_ico, name='favicon_ico'),
    path('favicon-192.png', favicon.favicon_png, name='favicon_png'),
    path('apple-touch-icon.png', favicon.apple_touch_icon, name='apple_touch_icon'),
    path('send-email/', views.send_contact_email, name='send_contact_email'),
    path('github-repos/', views.github_repos, name='github_repos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
