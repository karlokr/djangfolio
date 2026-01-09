from django.shortcuts import render
from projects.models import Project

# Create your views here.
def projects_list(request):
    projects = Project.objects.all()
    context = {
        'projects': projects,
    }
    return render(request, 'projects/projects_list.html', context)

def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    context = {
        'project': project,
    }
    return render(request, 'projects/project_detail.html', context)