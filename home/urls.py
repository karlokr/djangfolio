from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

from home import views

app_name = 'home'
urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('send-email/', views.send_contact_email, name='send_contact_email'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
