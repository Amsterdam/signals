# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.template import Context, Template
from django.test import TestCase


class TestMarkdownTemplateTags(TestCase):
    def test_markdown(self):
        context = Context({'body': '**Example**'})
        template = Template('{% load markdown_filters %}{{ body|markdown }}')

        actual = template.render(context)
        expected = '<p><strong>Example</strong></p>'
        self.assertEqual(expected, actual)

    def test_markdown_unsafe(self):
        context = Context({'body': '**Example** <script>alert("evil");</script>'})
        template = Template('{% load markdown_filters %}{{ body|markdown }}')

        actual = template.render(context)
        expected = '<p><strong>Example</strong> &lt;script&gt;alert(&quot;evil&quot;);&lt;/script&gt;</p>'
        self.assertEqual(expected, actual)

    def test_plaintext(self):
        context = Context({'body': '**Example**'})
        template = Template('{% load markdown_filters %}{{ body|plaintext }}')

        actual = template.render(context)
        expected = 'Example'
        self.assertEqual(expected, actual)

    def test_plaintext_unsafe(self):
        context = Context({'body': '**Example** <script>alert("evil");</script>'})
        template = Template('{% load markdown_filters %}{{ body|plaintext }}')

        actual = template.render(context)
        expected = 'Example alert(&quot;evil&quot;);'
        self.assertEqual(expected, actual)

    def test_markdown_drops_link_with_disallowed_scheme(self):
        # The rendered email is also what the backoffice shows as an email preview, where this href
        # would be a live link in a browser.
        context = Context({'body': '[Klik hier voor meer informatie](javascript:alert(1))'})
        template = Template('{% load markdown_filters %}{{ body|markdown }}')

        actual = template.render(context)
        expected = '<p><a>Klik hier voor meer informatie</a></p>'
        self.assertEqual(expected, actual)

    def test_markdown_keeps_link_with_allowed_scheme(self):
        context = Context({'body': 'Kijk op [amsterdam.nl](https://amsterdam.nl)'})
        template = Template('{% load markdown_filters %}{{ body|markdown }}')

        actual = template.render(context)
        expected = '<p>Kijk op <a href="https://amsterdam.nl">amsterdam.nl</a></p>'
        self.assertEqual(expected, actual)

    def test_plaintext_drops_link_with_disallowed_scheme(self):
        context = Context({'body': '[Klik hier voor meer informatie](javascript:alert(1))'})
        template = Template('{% load markdown_filters %}{{ body|plaintext }}')

        actual = template.render(context)
        expected = 'Klik hier voor meer informatie'
        self.assertEqual(expected, actual)
