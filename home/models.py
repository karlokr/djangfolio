from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

class SiteConfiguration(models.Model):
    """
    Singleton model to store site-wide configuration settings.
    This centralizes all PII and configurable site settings.
    Only one instance should exist.
    """
    # Personal Information
    full_name = models.CharField(
        max_length=100, 
        default='Your Name',
        help_text='Full name displayed on the site'
    )
    
    # Email Addresses
    contact_email = models.EmailField(
        default='contact@example.com',
        help_text='Email address where contact form submissions are sent'
    )
    display_email = models.EmailField(
        default='hello@example.com',
        help_text='Email address displayed publicly on the site'
    )
    
    # Social Media Links
    github_username = models.CharField(
        max_length=100,
        default='yourusername',
        help_text='GitHub username (without @) - used for API calls'
    )
    github_url = models.URLField(
        default='https://github.com/yourusername',
        help_text='Full GitHub profile URL'
    )
    linkedin_username = models.CharField(
        max_length=100,
        default='yourusername',
        help_text='LinkedIn username'
    )
    linkedin_url = models.URLField(
        default='https://www.linkedin.com/in/yourusername/',
        help_text='Full LinkedIn profile URL'
    )
    
    # Copyright Information
    copyright_text = models.CharField(
        max_length=200,
        default='Your Name. All rights reserved',
        help_text='Copyright text displayed in footer'
    )
    
    # Profile Image
    profile_image = models.ImageField(
        upload_to='profile/',
        blank=True,
        null=True,
        help_text='Profile image (recommended size: 400x400px or larger, square aspect ratio)'
    )
    profile_image_alt_text = models.CharField(
        max_length=100,
        default='Profile Photo',
        help_text='Alt text for profile image (for accessibility)'
    )
    
    # Favicon
    favicon = models.ImageField(
        upload_to='favicon/',
        blank=True,
        null=True,
        help_text='Site favicon (recommended size: 32x32px or 64x64px, .png or .ico format)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError('Only one Site Configuration instance is allowed. Please edit the existing one.')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_solo(cls):
        """Get the singleton instance, create with defaults if doesn't exist"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f'Site Configuration for {self.full_name}'

