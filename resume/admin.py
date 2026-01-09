from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedTabularInline, NestedModelAdmin
from resume.models import *

# Register your models here.
class ExpertiseInline(NestedStackedInline):
    model = ExpertiseItem
    inlines = []
    extra = 1

class SkillInline(NestedTabularInline):
    model = Skill
    inlines = []
    extra = 1

class EducationInline(NestedStackedInline):
    model = Education
    inlines = []
    extra = 1

class WorkExpItemInline(NestedStackedInline):
    model = WorkExperienceItem
    fk_name = 'experience'
    inlines = []
    extra = 1

class WorkExpInline(NestedStackedInline):
    model = WorkExperience
    extra = 1
    fk_name = 'resume'
    inlines = [WorkExpItemInline]

class AcademicExpItemInline(NestedStackedInline):
    model = AcademicExperienceItem
    fk_name = 'experience'
    inlines = []
    extra = 1

class AcademicExpInline(NestedStackedInline):
    model = AcademicExperience
    extra = 1
    fk_name = 'resume'
    inlines = [AcademicExpItemInline]

class ProjectExpItemInline(NestedStackedInline):
    model = ResumeProjectExperienceItem
    fk_name = 'experience'
    inlines = []
    extra = 1

class ProjectInline(NestedStackedInline):
    model = ResumeProject
    extra = 1
    fk_name = 'resume'
    inlines = [ProjectExpItemInline]

class VolunteerExpItemInline(NestedStackedInline):
    model = VolunteerExperienceItem
    fk_name = 'experience'
    inlines = []
    extra = 1

class VolunteerWorkInline(NestedStackedInline):
    model = VolunteerWork
    extra = 1
    fk_name = 'resume'
    inlines = [VolunteerExpItemInline]

class ResumeAdmin(NestedModelAdmin):
    model = Resume
    inlines = [ExpertiseInline, SkillInline, EducationInline, WorkExpInline,
               AcademicExpInline, ProjectInline, VolunteerWorkInline]
    
    def has_add_permission(self, request):
        """Only allow one instance"""
        return not Resume.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton instance"""
        return False

admin.site.register(Resume, ResumeAdmin)
admin.site.register(SkillGroup)

