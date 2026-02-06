from django.contrib import admin
from .models import BlogPost, BlogCategory, BlogTag


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_date', 'published']
    list_filter = ['published', 'created_date', 'categories']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_date'
    filter_horizontal = ['categories', 'tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'excerpt')
        }),
        ('Content', {
            'fields': ('content', 'featured_image')
        }),
        ('Organization', {
            'fields': ('categories', 'tags')
        }),
        ('Publishing', {
            'fields': ('published', 'created_date')
        }),
    )


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
