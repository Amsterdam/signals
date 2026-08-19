# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
import markdown
import pytest

from signals.apps.email_integrations.markdown.escaping import escape_markdown_link_syntax
from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html


class TestEscapeMarkdownLinkSyntax:
    @pytest.mark.parametrize('text', [
        '[Klik hier voor meer informatie](javascript:alert(1))',
        '[Bel ons](tel:0900-1234)',
        '[Bel ons](https://amsterdam.nl)',
        '![alt](https://amsterdam.nl/x.png)',
        '[Bel ons][ref]\n\n[ref]: tel:0900-1234',
        # A reporter escaping our escape: their backslash has to stay their backslash.
        '\\[Bel ons](tel:0900-1234)',
    ])
    def test_reporter_text_cannot_produce_a_link(self, text):
        html = markdown.markdown(escape_markdown_link_syntax(text))

        assert '<a' not in html
        assert '<img' not in html

    @pytest.mark.parametrize('text', [
        '[Klik hier voor meer informatie](javascript:alert(1))',
        'Er ligt afval bij nummer 12, kosten 10-20 euro.',
        'Zie de melding [nummer 3] van vorige week.',
    ])
    def test_reporter_text_stays_readable(self, text):
        plaintext = strip_markdown_html(markdown.markdown(escape_markdown_link_syntax(text)))

        assert plaintext == text

    def test_text_without_link_characters_is_left_alone(self):
        text = 'Er ligt afval op de stoep, ongeveer 10 meter voorbij nummer 12.'

        assert escape_markdown_link_syntax(text) == text
