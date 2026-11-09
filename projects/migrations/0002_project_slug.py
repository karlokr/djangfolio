from django.db import migrations, models
from django.utils.text import slugify


def fill_slugs(apps, schema_editor):
    """Give every existing project a unique slug from its title (as Project.save does)."""
    Project = apps.get_model('projects', 'Project')
    taken = set()
    for project in Project.objects.order_by('pk'):
        base = slugify(project.title)[:190] or 'project'
        if base.isdigit():
            base = f'project-{base}'
        slug, n = base, 2
        while slug in taken:
            slug, n = f'{base}-{n}', n + 1
        taken.add(slug)
        project.slug = slug
        project.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, null=True),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=models.SlugField(blank=True, help_text="The project page's address: /projects/<slug>/. Filled in from the title when left blank. Changing it breaks existing links.", max_length=200, unique=True),
        ),
    ]
