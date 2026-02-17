import re

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from markdownx.utils import markdownify
from .models import BlogPost, BlogCategory, BlogTag
from resume.models import Resume


def _markdownify_with_math(content):
    """Convert Markdown to HTML while preserving LaTeX math blocks.

    The standard Markdown processor treats backslashes as escape characters
    and underscores as emphasis markers, which corrupts LaTeX.  This helper
    extracts ``$$…$$`` and ``$…$`` spans before processing, replaces them
    with unique placeholders, runs *markdownify*, then restores the originals.

    Dollar-sign delimiters are converted to ``\\[…\\]`` (display) and
    ``\\(…\\)`` (inline) so that literal ``$`` in the final HTML is never
    ambiguous with currency symbols like $100 or $HACHI.
    """
    placeholders = {}
    counter = [0]

    def _placeholder(match, display=False):
        """Replace a math span with a unique key and store the converted form."""
        raw = match.group(0)
        inner = match.group(1)
        counter[0] += 1
        key = f"MATHBLOCK{counter[0]}"
        if display:
            placeholders[key] = f"\\[{inner}\\]"
        else:
            placeholders[key] = f"\\({inner}\\)"
        return key

    # 1. Display math  $$…$$  (may span multiple lines)
    protected = re.sub(
        r'\$\$(.+?)\$\$',
        lambda m: _placeholder(m, display=True),
        content,
        flags=re.DOTALL,
    )

    # 2. Inline math  $…$  – must contain a backslash OR be short & start
    #    with a letter so we never match currency like $100 or $HACHI.
    def _inline_placeholder(match):
        return _placeholder(match, display=False)

    #    Pattern A: contains a backslash  (e.g. $\frac{a}{b}$)
    protected = re.sub(r'\$(?!\$)([^$\n]*?\\[^$\n]*?)\$', _inline_placeholder, protected)
    #    Pattern B: short (1-10 chars), starts with a letter  (e.g. $k$, $x_i$)
    protected = re.sub(r'\$(?!\$)([a-zA-Z][^$\n]{0,8}?)\$', _inline_placeholder, protected)

    # 3. Also protect existing \[…\] and \(…\) from Markdown mangling
    protected = re.sub(
        r'\\\[(.+?)\\\]',
        lambda m: _placeholder(m, display=True),
        protected,
        flags=re.DOTALL,
    )
    protected = re.sub(
        r'\\\((.+?)\\\)',
        lambda m: _placeholder(m, display=False),
        protected,
    )

    html = markdownify(protected)

    for key in sorted(placeholders, key=len, reverse=True):
        html = html.replace(key, placeholders[key])

    return html


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
        'post_content_html': _markdownify_with_math(post.content),
        'related_posts': related_posts,
        'resume': resume,
        'active_page': 'blog',
    }
    
    # Return partial template for HTMX requests
    template = 'blog/blog_detail_partial.html' if request.htmx else 'blog/blog_detail.html'
    return render(request, template, context)
