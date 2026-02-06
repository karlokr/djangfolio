from django.shortcuts import render
from projects.models import Project

# Create your views here.
def projects_list(request):
    projects = Project.objects.all()
    context = {
        'projects': projects,
        'active_page': 'projects',
    }
    # Return partial template for HTMX requests
    template = 'projects/projects_list_partial.html' if request.htmx else 'projects/projects_list.html'
    return render(request, template, context)

def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    context = {
        'project': project,
        'active_page': 'projects',
    }
    # Return partial template for HTMX requests
    template = 'projects/project_detail_partial.html' if request.htmx else 'projects/project_detail.html'
    return render(request, template, context)