from django.core.management.base import BaseCommand
from blog.models import BlogPost, BlogCategory, BlogTag
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import random


class Command(BaseCommand):
    help = 'Creates fake blog posts for testing'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, nargs='?', default=10, help='Number of posts to create')

    def handle(self, *args, **options):
        count = options['count']
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('admin', 'admin@example.com', 'admin')
            self.stdout.write(f'Created admin user')

        # Get existing categories and tags
        categories = list(BlogCategory.objects.all())
        tags = list(BlogTag.objects.all())

        # Sample titles and excerpts to mix and match
        titles = [
            'Getting Started with {}',
            'Advanced {} Techniques',
            'Introduction to {}',
            '{} Best Practices',
            'Building with {}',
            'Mastering {}',
            '{} for Beginners',
            'Deep Dive into {}',
            'Understanding {}',
            '{} Tips and Tricks',
            'The Complete {} Guide',
            '{} Fundamentals',
            'Modern {} Development',
            '{} Patterns',
            'Optimizing {}',
        ]
        
        topics = [
            'Django', 'Python', 'Machine Learning', 'Docker', 'REST APIs',
            'PostgreSQL', 'React', 'CI/CD', 'Cloud Computing', 'Kubernetes',
            'Data Science', 'Web Security', 'TypeScript', 'GraphQL', 'Redis',
            'MongoDB', 'Git', 'Linux', 'AWS', 'Azure', 'FastAPI', 'Vue.js',
            'Testing', 'Microservices', 'DevOps', 'Serverless', 'WebSockets',
        ]
        
        excerpts = [
            'Learn the essentials and build your first application.',
            'Essential practices every developer should know.',
            'A comprehensive guide to understanding core concepts.',
            'How to effectively leverage this technology in your projects.',
            'Create robust solutions with industry best practices.',
            'Improve your skills with these proven techniques.',
            'Build modern applications with confidence.',
            'Automate and streamline your development workflow.',
            'Understanding services and how to leverage them.',
            'Master the fundamentals and beyond.',
            'Explore analysis and implementation strategies.',
            'Protect your applications and write secure code.',
        ]

        created_count = 0
        for i in range(count):
            title_template = random.choice(titles)
            topic = random.choice(topics)
            title = title_template.format(topic)
            excerpt = random.choice(excerpts)
            
            # Generate unique slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            
            post = BlogPost.objects.create(
                title=title,
                slug=slug,
                excerpt=excerpt,
                content=f"<p>{excerpt}</p><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p><p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>",
                author=user,
                published=True,
            )
            
            # Add random categories and tags
            if categories:
                post.categories.set(random.sample(categories, min(random.randint(1, 3), len(categories))))
            if tags:
                post.tags.set(random.sample(tags, min(random.randint(2, 5), len(tags))))
            
            created_count += 1
            self.stdout.write(f'Created: {post.title}')

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new blog posts. Total posts: {BlogPost.objects.count()}'))
