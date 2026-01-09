from django.contrib import admin
from projects.models import *

class FeatureInline(admin.StackedInline):
    model = ProjectFeature
    extra = 1

class SpecialThanksInline(admin.StackedInline):
    model = ProjectSpecialThanks
    extra = 1

class TeammatesInline(admin.StackedInline):
    model = ProjectTeammate
    extra = 1

class ImageInline(admin.StackedInline):
    model = ProjectImage
    extra = 1

class VideoInline(admin.StackedInline):
    model = ProjectVideo
    extra = 1

class GithubLinkInline(admin.StackedInline):
    model = GitHubProjectLink
    extra = 1

class CompanyLinkInline(admin.StackedInline):
    model = CompanyProjectLink
    extra = 1

class LiveLinkInline(admin.StackedInline):
    model = LiveProjectLink
    extra = 1

class InstitutionLinkInline(admin.StackedInline):
    model = InstitutionProjectLink
    extra = 1

class WebsiteLinkInline(admin.StackedInline):
    model = WebsiteProjectLink
    extra = 1

class PlayStoreLinkInline(admin.StackedInline):
    model = PlayStoreProjectLink
    extra = 1

class MathPhysicsProjectAdmin(admin.ModelAdmin):
    model = MathPhysicsProject
    inlines = [
        FeatureInline, SpecialThanksInline, 
        TeammatesInline, ImageInline, VideoInline,
        CompanyLinkInline, WebsiteLinkInline, GithubLinkInline,
        InstitutionLinkInline, LiveLinkInline, PlayStoreLinkInline,
    ]

class WebProjectAdmin(admin.ModelAdmin):
    model = WebProject
    inlines = [
        FeatureInline, SpecialThanksInline, 
        TeammatesInline, ImageInline, VideoInline,
        CompanyLinkInline, WebsiteLinkInline, GithubLinkInline,
        InstitutionLinkInline, LiveLinkInline, PlayStoreLinkInline,
    ]

class SoftwareProjectAdmin(admin.ModelAdmin):
    model = SoftwareProject
    inlines = [
        FeatureInline, SpecialThanksInline, 
        TeammatesInline, ImageInline, VideoInline,
        CompanyLinkInline, WebsiteLinkInline, GithubLinkInline,
        InstitutionLinkInline, LiveLinkInline, PlayStoreLinkInline,
    ]

admin.site.register(SoftwareProject, SoftwareProjectAdmin)
admin.site.register(WebProject, WebProjectAdmin)
admin.site.register(MathPhysicsProject, MathPhysicsProjectAdmin)
