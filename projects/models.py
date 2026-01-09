from django.db import models
from django.utils import timezone

class Project(models.Model):
    title = models.CharField(max_length=200)
    short_description = models.TextField()
    long_description = models.TextField()
    technology = models.CharField(max_length=50, default=None, blank=True, null=True)
    css_id = models.CharField(max_length=75)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

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

