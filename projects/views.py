from django.shortcuts import get_object_or_404, render
from projects.models import Project
from home import seo
from home.models import SiteConfiguration
from home.templatetags.custom_filters import seo_description
from portfolio.htmx import wants_partial

# Create your views here.
def projects_list(request):
    projects = Project.objects.all()
    name = SiteConfiguration.get_solo().full_name
    context = {
        'page_title': seo.page_title('Projects', name),
        'page_description': seo.listing_description(
            f'Projects by {name}', [p.title for p in projects], connector='including'
        ),
        'projects': projects,
        'active_page': 'projects',
    }
    # Return partial template for HTMX requests
    template = 'projects/projects_list_partial.html' if wants_partial(request) else 'projects/projects_list.html'
    return render(request, template, context)

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    context = {
        'page_title': seo.page_title(project.title, SiteConfiguration.get_solo().full_name),
        'page_description': seo_description(project.short_description),
        'project': project,
        'active_page': 'projects',
    }
    # Return partial template for HTMX requests
    template = 'projects/project_detail_partial.html' if wants_partial(request) else 'projects/project_detail.html'
    return render(request, template, context)