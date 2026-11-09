from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def project_slug_base(title):
    """The slug a title starts from. Never only digits, which would read as
    an old numeric address (/projects/<id>/ redirects to /projects/<slug>/)."""
    base = slugify(title)[:190] or 'project'
    return f'project-{base}' if base.isdigit() else base


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text='The project page\'s address: /projects/<slug>/. Filled in from '
                  'the title when left blank. Changing it breaks existing links.'
    )
    short_description = models.TextField()
    long_description = models.TextField()
    technology = models.CharField(max_length=50, default=None, blank=True, null=True)
    css_id = models.CharField(max_length=75)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = project_slug_base(self.title)
            slug, n = base, 2
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects:project_detail', args=[self.slug])

class SoftwareProject(Project):
    project_type = models.CharField(max_length=30, default='Software Project')

class WebProject(Project):
    project_type = models.CharField(max_length=30, default='Web/Mobile Project')

class MathPhysicsProject(Project):
    project_type = models.CharField(max_length=30, default='Math & Physics Project')
    preview_type = models.CharField(max_length=10, default='pdf')

class ProjectLink(models.Model):
    exact_url = models.CharField(max_length=100)
    pretty_url = models.CharField(max_length=100)
    text = models.CharField(max_length=100)

class GitHubProjectLink(ProjectLink):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class CompanyProjectLink(ProjectLink):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class LiveProjectLink(ProjectLink):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class InstitutionProjectLink(ProjectLink):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class WebsiteProjectLink(ProjectLink):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class PlayStoreProjectLink(ProjectLink):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    
class ProjectFeature(models.Model):
    text = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class ProjectSpecialThanks(models.Model):
    text = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class ProjectTeammate(models.Model):
    text = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class ProjectVideo(models.Model):
    video = models.CharField(max_length=256)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

class ProjectImage(models.Model):
    image = models.ImageField(upload_to='projects/%Y/%m/%d')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

