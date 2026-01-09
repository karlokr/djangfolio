from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Create your models here.
class Resume(models.Model):
    """
    Singleton model for resume information.
    Only one instance should exist.
    """
    name = models.CharField(max_length=20)
    headline = models.CharField(max_length=30)
    location = models.CharField(max_length=30)
    about_text = models.TextField()
    github_link = models.CharField(max_length=256, default='')
    github_username = models.CharField(max_length=30, default='')
    linkedin_link = models.CharField(max_length=256, default='')
    email = models.CharField(max_length=100, default='')

    class Meta:
        verbose_name = 'Resume'
        verbose_name_plural = 'Resume'

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if not self.pk and Resume.objects.exists():
            raise ValidationError('Only one Resume instance is allowed. Please edit the existing one.')
        return super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Get the singleton instance, create with defaults if doesn't exist"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.name

class ExpertiseItem(models.Model):
    text = models.TextField()
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)

    def __str__(self):
        return '#' + str(self.pk)

class SkillGroup(models.Model):
    skill_group = models.CharField(max_length=50)

    def __str__(self):
        return self.skill_group

class Skill(models.Model):
    skill = models.CharField(max_length=30)
    skill_group = models.ForeignKey(SkillGroup, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)

    def __str__(self):
        return self.skill

class Education(models.Model):
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    location = models.CharField(max_length=30)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)

    def __str__(self):
        return self.degree

class WorkExperience(models.Model):
    title = models.CharField(max_length=50)
    company = models.CharField(max_length=50)
    location = models.CharField(max_length=30)
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '#' + str(self.pk)

    class Meta:
        ordering = ['-pub_date']

class WorkExperienceItem(models.Model):
    text = models.CharField(max_length=500)
    experience = models.ForeignKey(WorkExperience, on_delete=models.CASCADE)

    def __str__(self):
        return '#' + str(self.pk)

class AcademicExperience(models.Model):
    experience_type = models.CharField(max_length=50)
    course = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '#' + str(self.pk)

    class Meta:
        ordering = ['-pub_date']


class AcademicExperienceItem(models.Model):
    text = models.CharField(max_length=500)
    experience = models.ForeignKey(AcademicExperience, on_delete=models.CASCADE)

    def __str__(self):
        return '#' + str(self.pk)

class ResumeProject(models.Model):
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    start_date = models.CharField(max_length=20)
    end_date = models.CharField(max_length=20)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '#' + str(self.pk)

    class Meta:
        ordering = ['-pub_date']


class ResumeProjectExperienceItem(models.Model):
    text = models.CharField(max_length=500)
    experience = models.ForeignKey(ResumeProject, on_delete=models.CASCADE)

    def __str__(self):
        return '#' + str(self.pk)

class VolunteerWork(models.Model):
    title = models.CharField(max_length=50)
    institution = models.CharField(max_length=50)
    location = models.CharField(max_length=30)
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '#' + str(self.pk)

    class Meta:
        ordering = ['-pub_date']


class VolunteerExperienceItem(models.Model):
    text = models.CharField(max_length=500)
    experience = models.ForeignKey(VolunteerWork, on_delete=models.CASCADE)

    def __str__(self):
        return '#' + str(self.pk)
