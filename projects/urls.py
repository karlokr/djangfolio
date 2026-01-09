from django.urls import include, path

from projects import views

app_name = 'projects'
urlpatterns = [
    path('', views.projects_list, name='projects_list'),
    path('<int:pk>/', views.project_detail, name='project_detail')
]
