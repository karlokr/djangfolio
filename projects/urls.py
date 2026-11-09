from django.urls import include, path

from projects import views

app_name = 'projects'
urlpatterns = [
    path('', views.projects_list, name='projects_list'),
    # The old numeric addresses redirect to the slug ones; before the slug
    # pattern, which digits would also match.
    path('<int:pk>/', views.project_detail_by_id, name='project_detail_by_id'),
    path('<slug:slug>/', views.project_detail, name='project_detail'),
]
