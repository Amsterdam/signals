# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import os

import mistune
import pytest
from mistune import Markdown

from signals.apps.email_integrations.markdown.renderers import PlaintextRenderer


class TestPlaintextRenderer:
    @pytest.fixture
    def render_plaintext(self) -> Markdown:
        return mistune.create_markdown(renderer=PlaintextRenderer())

    def test_text(self, render_plaintext: Markdown):
        markdown = 'This is just some plain old regular text'
        expected = 'This is just some plain old regular text\n'

        assert expected == render_plaintext(markdown)

    def test_link(self, render_plaintext: Markdown):
        markdown = '[Example](https://www.example.com)'
        expected = 'Example https://www.example.com\n'

        assert expected == render_plaintext(markdown)

    def test_heading(self, render_plaintext: Markdown):
        markdown = '# First heading\n## Second heading'
        expected = 'First heading\n\nSecond heading\n'

        assert expected == render_plaintext(markdown)

    def test_bold(self, render_plaintext: Markdown):
        markdown = '**Bold**'
        expected = 'Bold\n'

        assert expected == render_plaintext(markdown)

    def test_italic(self, render_plaintext: Markdown):
        markdown = '*Italic*'
        expected = 'Italic\n'

        assert expected == render_plaintext(markdown)

    def test_list(self, render_plaintext: Markdown):
        markdown = '- First\n- Second'
        expected = '- First\n- Second\n'

        assert expected == render_plaintext(markdown)

    def test_image(self, render_plaintext: Markdown):
        markdown = '![Alternative text](image.png)'
        expected = 'Alternative text\n'

        assert expected == render_plaintext(markdown)

    def test_lots_of_markdown(self, render_plaintext: Markdown):
        path = os.path.dirname(os.path.abspath(__file__))
        markdown = open(os.path.join(path, 'lots_of.md'), 'r').read()
        expected = open(os.path.join(path, 'lots_of.txt'), 'r').read()

        assert expected == render_plaintext(markdown)
