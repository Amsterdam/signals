# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.template import Context, Template
from django.test import TestCase


class TestMarkdownTemplateTags(TestCase):
    def test_markdown(self):
        context = Context({'body': '**Example**'})
        template = Template('{% load markdown %}{{ body|markdown }}')

        actual = template.render(context)
        expected = '<p><strong>Example</strong></p>\n'
        self.assertEqual(expected, actual)

    def test_markdown_unsafe(self):
        context = Context({'body': '**Example** <script>alert("evil");</script>'})
        template = Template('{% load markdown %}{{ body|markdown }}')

        actual = template.render(context)
        expected = '<p><strong>Example</strong> &lt;script&gt;alert(&quot;evil&quot;);&lt;/script&gt;</p>\n'
        self.assertEqual(expected, actual)

    def test_plaintext(self):
        context = Context({'body': '**Example**'})
        template = Template('{% load markdown %}{{ body|plaintext }}')

        actual = template.render(context)
        expected = 'Example\n\n'
        self.assertEqual(expected, actual)

    def test_plaintext_unsafe(self):
        context = Context({'body': '**Example** <script>alert("evil");</script>'})
        template = Template('{% load markdown %}{{ body|plaintext }}')

        actual = template.render(context)
        expected = 'Example alert(&quot;evil&quot;);\n\n'
        self.assertEqual(expected, actual)
