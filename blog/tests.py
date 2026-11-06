from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase

from blog.math_markdown import markdownify_with_math
from blog.models import BlogTag


class BlogListCrawlerTests(TestCase):
    """Filtered blog lists are endless for crawlers, so they're kept out."""

    def setUp(self):
        BlogTag.objects.get_or_create(slug='python', defaults={'name': 'Python'})

    def test_unfiltered_list_is_indexable(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('X-Robots-Tag', response)
        self.assertNotContains(response, 'name="robots"')

    def test_filtered_list_is_noindex_with_canonical(self):
        response = self.client.get('/blog/?tag=python&category=misc')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')
        self.assertContains(response, '<meta name="robots" content="noindex, nofollow">')
        self.assertContains(response, '<link rel="canonical" href="http://testserver/blog/">')

    def test_filtered_partial_sends_header(self):
        response = self.client.get('/blog/?tag=python', HTTP_HX_REQUEST='true')
        self.assertEqual(response['X-Robots-Tag'], 'noindex, nofollow')

    def test_filter_links_are_nofollow(self):
        response = self.client.get('/blog/')
        self.assertContains(response, '<a rel="nofollow" href="/blog/?tag=python&"')


class MathMarkdownTests(SimpleTestCase):
    """$ is inline math only under Pandoc's rules; money stays text."""

    def render(self, text):
        return markdownify_with_math(text)

    def assertNoMath(self, text):
        html = self.render(text)
        self.assertNotIn('\\(', html)
        self.assertNotIn('\\[', html)
        return html

    def test_money_is_not_math(self):
        for text in [
            'It costs $100.',
            'Between $5 and $10 a month.',
            'Buy $HACHI with SOL, then sell $HACHI.',
            'A $1.5M round.',
            'Gas was $5-$50 per transaction.',
            "That's $1,100 per day split among $100K of liquidity.",
            '| WSOL/pippin ($16M TVL) | 101% |',
        ]:
            with self.subTest(text=text):
                html = self.assertNoMath(text)
                self.assertEqual(html.count('$'), text.count('$'))

    def test_inline_math(self):
        self.assertEqual(self.render('Let $x_i$ be $\\frac{a}{b}$.'),
                         '<p>Let \\(x_i\\) be \\(\\frac{a}{b}\\).</p>')

    def test_inline_math_next_to_money(self):
        self.assertEqual(self.render('Pay $5 when $k$ is odd.'),
                         '<p>Pay $5 when \\(k\\) is odd.</p>')

    def test_inline_math_needs_tight_delimiters(self):
        self.assertNoMath('$ x$ and $x $')

    def test_closing_dollar_not_followed_by_digit(self):
        self.assertNoMath('From $x$5 onwards')

    def test_inline_math_does_not_cross_paragraphs(self):
        self.assertNoMath('Costs $5\n\nand $10')

    def test_paren_inline_math(self):
        self.assertEqual(self.render('Where \\(r_f\\) is the APR'),
                         '<p>Where \\(r_f\\) is the APR</p>')

    def test_display_math(self):
        self.assertEqual(self.render('$$x \\times y = k$$'), '<p>\\[x \\times y = k\\]</p>')
        self.assertEqual(self.render('\\[a_1 *b* c_2\\]'), '<p>\\[a_1 *b* c_2\\]</p>')

    def test_display_math_spans_lines(self):
        self.assertEqual(self.render('$$\na_1 \\\\\nb_2\n$$'), '<p>\\[\na_1 \\\\\nb_2\n\\]</p>')

    def test_dollar_inside_display_math(self):
        self.assertEqual(self.render('$$\\$500 \\times 2$$'), '<p>\\[\\$500 \\times 2\\]</p>')

    def test_escaped_dollar_is_literal(self):
        self.assertEqual(self.render('Costs \\$5 and \\$x\\$.'), '<p>Costs $5 and $x$.</p>')

    def test_math_is_html_escaped(self):
        self.assertEqual(self.render('$a<b$'), '<p>\\(a&lt;b\\)</p>')

    def test_code_is_left_alone(self):
        html = self.assertNoMath('Call `$this->name` or `` $a$ ``.')
        self.assertIn('<code>$this-&gt;name</code>', html)
        html = self.assertNoMath('```bash\necho $HOME $x$ \\$y\n```')
        self.assertIn('echo $HOME $x$ \\$y', html)

    def test_frontend_has_no_dollar_delimiters(self):
        """KaTeX auto-render only gets the delimiters the server emits."""
        source = (Path(settings.BASE_DIR) / 'home/templates/base_layout.html').read_text()
        self.assertIn("{left: '\\\\(', right: '\\\\)', display: false}", source)
        self.assertIn("{left: '\\\\[', right: '\\\\]', display: true}", source)
        self.assertNotIn("left: '$", source)
        self.assertEqual(source.count('renderMathInElement('), 1)
