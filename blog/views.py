from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import BlogPost, BlogCategory, BlogTag
from resume.models import Resume


def blog_list(request):
    """Display list of published blog posts with pagination."""
    posts = BlogPost.objects.filter(published=True)
    
    # Filter by categories and/or tags if provided (OR logic - matches any)
    category_slugs = request.GET.getlist('category')
    tag_slugs = request.GET.getlist('tag')
    
    if category_slugs or tag_slugs:
        filter_q = Q()
        if category_slugs:
            filter_q |= Q(categories__slug__in=category_slugs)
        if tag_slugs:
            filter_q |= Q(tags__slug__in=tag_slugs)
        posts = posts.filter(filter_q).distinct()
    
    # Pagination
    paginator = Paginator(posts, 4)  # 4 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Compute consistent page range (always show 5 pages if available)
    num_pages = paginator.num_pages
    current_page = page_obj.number
    max_visible = 5
    
    if num_pages <= max_visible:
        page_range = range(1, num_pages + 1)
    else:
        # Calculate start and end, keeping current page centered when possible
        start = max(1, current_page - max_visible // 2)
        end = start + max_visible - 1
        
        # Adjust if we're near the end
        if end > num_pages:
            end = num_pages
            start = end - max_visible + 1
        
        page_range = range(start, end + 1)
    
    # Get all categories and tags for sidebar with post counts, sorted by count
    categories = BlogCategory.objects.annotate(
        post_count=Count('posts', filter=Q(posts__published=True))
    ).order_by('-post_count', 'name')
    tags = BlogTag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__published=True))
    ).order_by('-post_count', 'name')
    
    # Get actual selected category/tag objects for display
    selected_category_objects = BlogCategory.objects.filter(slug__in=category_slugs) if category_slugs else []
    selected_tag_objects = BlogTag.objects.filter(slug__in=tag_slugs) if tag_slugs else []
    
    context = {
        'page_obj': page_obj,
        'page_range': page_range,
        'categories': categories,
        'tags': tags,
        'selected_categories': category_slugs,
        'selected_tags': tag_slugs,
        'selected_category_objects': selected_category_objects,
        'selected_tag_objects': selected_tag_objects,
        'active_page': 'blog',
    }
    
    # Return partial template for HTMX requests
    template = 'blog/blog_list_partial.html' if request.htmx else 'blog/blog_list.html'
    return render(request, template, context)


def blog_detail(request, slug):
    """Display a single blog post."""
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    resume = Resume.get_solo()
    
    # Get related posts (same category)
    related_posts = BlogPost.objects.filter(
        published=True,
        categories__in=post.categories.all()
    ).exclude(id=post.id).distinct()[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'resume': resume,
        'active_page': 'blog',
    }
    
    # Return partial template for HTMX requests
    template = 'blog/blog_detail_partial.html' if request.htmx else 'blog/blog_detail.html'
    return render(request, template, context)
