from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


def get_default_author():
    """Get default author name from site configuration."""
    from home.models import SiteConfiguration
    try:
        return SiteConfiguration.get_solo().full_name
    except Exception:
        return "Admin"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    excerpt = models.TextField(max_length=300, help_text="Short description for the blog list")
    content = CKEditor5Field('Content', config_name='extends', help_text="Main blog content with rich text and images")
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    author = models.CharField(max_length=100, default=get_default_author)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_date']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Blog Categories"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class BlogTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


# Update BlogPost to include categories and tags
BlogPost.add_to_class('categories', models.ManyToManyField(BlogCategory, blank=True, related_name='posts'))
BlogPost.add_to_class('tags', models.ManyToManyField(BlogTag, blank=True, related_name='posts'))
