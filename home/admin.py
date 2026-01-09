from django.contrib import admin
from .models import SiteConfiguration

# Register your models here.

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for Site Configuration"""
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'profile_image', 'profile_image_alt_text')
        }),
        ('Email Addresses', {
            'fields': ('display_email', 'contact_email')
        }),
        ('GitHub', {
            'fields': ('github_username', 'github_url')
        }),
        ('LinkedIn', {
            'fields': ('linkedin_username', 'linkedin_url')
        }),
        ('Copyright', {
            'fields': ('copyright_text',)
        }),
    )
    
    def has_add_permission(self, request):
        """Only allow one instance"""
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton instance"""
        return False
