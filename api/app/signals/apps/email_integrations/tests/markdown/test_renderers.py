# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import mistune
from django.test import TestCase

from signals.apps.email_integrations.markdown.renderers import PlaintextRenderer


class TestPlaintextRenderer(TestCase):
    render_plaintext = None

    def setUp(self):
        self.render_plaintext = mistune.create_markdown(renderer=PlaintextRenderer())

    def test_headings(self):
        markdown = '# First heading\n## Second heading'
        expected = 'First heading\n\nSecond heading\n\n'

        self.assertEqual(expected, self.render_plaintext(markdown))

    def test_links(self):
        markdown = '[Example](https://www.example.com)'
        expected = 'Example https://www.example.com\n\n'

        self.assertEqual(expected, self.render_plaintext(markdown))

    def test_bold(self):
        markdown = '**Bold**'
        expected = 'Bold\n\n'

        self.assertEqual(expected, self.render_plaintext(markdown))

    def test_italic(self):
        markdown = '*Italic*'
        expected = 'Italic\n\n'

        self.assertEqual(expected, self.render_plaintext(markdown))

    def test_list(self):
        markdown = '- First\n- Second'
        expected = '- First\n- Second\n'

        self.assertEqual(expected, self.render_plaintext(markdown))

    def test_image(self):
        markdown = '![Alternative text](image.png)'
        expected = 'Alternative text\n\n'

        self.assertEqual(expected, self.render_plaintext(markdown))
