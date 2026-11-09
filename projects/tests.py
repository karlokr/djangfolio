from django.test import TestCase

from projects.models import Project


class ProjectAddressTests(TestCase):
    """Projects live at /projects/<slug>/; the old /projects/<id>/ redirects there."""

    def test_slug_from_title_and_unique(self):
        first = Project.objects.create(title='My Cool App', short_description='x',
                                       long_description='y', css_id='a')
        second = Project.objects.create(title='My Cool App', short_description='x',
                                        long_description='y', css_id='b')
        numeric = Project.objects.create(title='2048', short_description='x',
                                         long_description='y', css_id='c')
        self.assertEqual(first.slug, 'my-cool-app')
        self.assertEqual(second.slug, 'my-cool-app-2')
        self.assertEqual(numeric.slug, 'project-2048')
        self.assertEqual(first.get_absolute_url(), '/projects/my-cool-app/')

    def test_detail_by_slug_and_old_address_redirects(self):
        project = Project.objects.create(title='AutoThing', short_description='x',
                                         long_description='y', css_id='a')
        self.assertEqual(self.client.get('/projects/autothing/').status_code, 200)
        response = self.client.get(f'/projects/{project.pk}/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/projects/autothing/')
        self.assertEqual(self.client.get('/projects/999/').status_code, 404)
        self.assertEqual(self.client.get('/projects/no-such-project/').status_code, 404)

    def test_list_links_to_slug_addresses(self):
        Project.objects.create(title='AutoThing', short_description='x',
                               long_description='y', css_id='a')
        self.assertContains(self.client.get('/projects/'), 'href="/projects/autothing/"')


class ProjectsListIndexingTests(TestCase):
    """While the Projects link is hidden, the list stays out of search results."""

    def test_noindex_only_while_hidden(self):
        from home.models import SiteConfiguration

        config = SiteConfiguration.get_solo()
        config.show_projects_link = True
        config.save()
        self.assertNotContains(self.client.get('/projects/'), 'name="robots"')
        config.show_projects_link = False
        config.save()
        self.assertContains(self.client.get('/projects/'), '<meta name="robots" content="noindex, follow">')
