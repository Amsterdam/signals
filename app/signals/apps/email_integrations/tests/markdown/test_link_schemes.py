# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
import markdown
import pytest

from signals.apps.email_integrations.markdown.link_schemes import (
    LinkSchemeExtension,
    is_allowed_url
)


def render(text: str) -> str:
    return markdown.markdown(text, extensions=[LinkSchemeExtension()])


class TestIsAllowedUrl:
    @pytest.mark.parametrize('url', [
        'https://amsterdam.nl',
        'http://amsterdam.nl',
        'HTTPS://amsterdam.nl',
        'mailto:meldingen@amsterdam.nl',
        'tel:14020',
        '/relatief/pad',
        '#anker',
        '',
    ])
    def test_allowed(self, url):
        assert is_allowed_url(url) is True

    @pytest.mark.parametrize('url', [
        'javascript:alert(1)',
        'JavaScript:alert(1)',
        'data:text/html;base64,PHN2Zz4=',
        'vbscript:msgbox(1)',
        'file:///etc/passwd',
        'sms:0900-1234',
        'callto:0900-1234',
    ])
    def test_disallowed(self, url):
        assert is_allowed_url(url) is False

    @pytest.mark.parametrize('url', [
        ' javascript:alert(1)',
        '\tjavascript:alert(1)',
        'java\nscript:alert(1)',
        'java\x00script:alert(1)',
    ])
    def test_disallowed_when_the_scheme_is_hidden_behind_characters_a_browser_drops(self, url):
        assert is_allowed_url(url) is False


class TestLinkSchemeExtension:
    @pytest.mark.parametrize('text', [
        '[Klik hier](javascript:alert(1))',
        '[Klik hier](JAVASCRIPT:alert(1))',
        '[Klik hier](  javascript:alert(1))',
        '[Klik hier](vbscript:msgbox(1))',
        '[Klik hier](sms:0900-1234)',
        '<javascript:alert(1)>',
        '[Klik hier][ref]\n\n[ref]: javascript:alert(1)',
    ])
    def test_removes_the_destination_of_a_disallowed_link(self, text):
        assert 'href' not in render(text)

    def test_keeps_the_text_of_a_disallowed_link(self):
        assert render('[Klik hier](javascript:alert(1))') == '<p><a>Klik hier</a></p>'

    def test_removes_the_source_of_a_disallowed_image(self):
        assert render('![alt](data:text/html;base64,PHN2Zz4=)') == '<p><img alt="alt" /></p>'

    @pytest.mark.parametrize('text,expected', [
        ('[Bel](tel:14020)', '<p><a href="tel:14020">Bel</a></p>'),
        ('[Site](https://amsterdam.nl)', '<p><a href="https://amsterdam.nl">Site</a></p>'),
        ('[Mail](mailto:x@amsterdam.nl)', '<p><a href="mailto:x@amsterdam.nl">Mail</a></p>'),
        ('[Melding](/melding/1)', '<p><a href="/melding/1">Melding</a></p>'),
        ('![alt](https://amsterdam.nl/x.png)', '<p><img alt="alt" src="https://amsterdam.nl/x.png" /></p>'),
    ])
    def test_leaves_an_allowed_destination_alone(self, text, expected):
        assert render(text) == expected

    def test_leaves_markdown_that_is_not_a_link_alone(self):
        assert render('**Example**') == '<p><strong>Example</strong></p>'
