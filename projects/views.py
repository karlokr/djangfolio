from django.shortcuts import get_object_or_404, render
from projects.models import Project
from portfolio.htmx import wants_partial

# Create your views here.
def projects_list(request):
    projects = Project.objects.all()
    context = {
        'projects': projects,
        'active_page': 'projects',
    }
    # Return partial template for HTMX requests
    template = 'projects/projects_list_partial.html' if wants_partial(request) else 'projects/projects_list.html'
    return render(request, template, context)

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    context = {
        'project': project,
        'active_page': 'projects',
    }
    # Return partial template for HTMX requests
    template = 'projects/project_detail_partial.html' if wants_partial(request) else 'projects/project_detail.html'
    return render(request, template, context)