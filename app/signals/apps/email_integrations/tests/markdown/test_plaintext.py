# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import os

import markdown

from signals.apps.email_integrations.markdown.plaintext import strip_markdown_html


class TestStripMarkdownHtml:
    def test_lost_of_markdown(self):
        path = os.path.dirname(os.path.abspath(__file__))
        md = open(os.path.join(path, 'lots_of.md'), 'r').read()
        expected = open(os.path.join(path, 'lots_of.txt'), 'r').read()

        html = markdown.markdown(md)

        assert expected == strip_markdown_html(html)

    def test_external_reaction_received(self):
        md = """Geachte behandelaar,

Bedankt voor het invullen van het actieformulier. Uw informatie helpt ons bij het verwerken van de melding.

U liet ons het volgende weten:  
{{ reaction_text }}

Gegevens van de melding
- Nummer: {{ formatted_signal_id }}
- Gemeld op: {{ created_at|date:"DATETIME_FORMAT" }}
- Plaats: {% if location %}{{ location|format_address:"O hlT, P W" }}{% endif %}


Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte behandelaar,

Bedankt voor het invullen van het actieformulier. Uw informatie helpt ons bij het verwerken van de melding.

U liet ons het volgende weten:
{{ reaction_text }}

Gegevens van de melding
- Nummer: {{ formatted_signal_id }}
- Gemeld op: {{ created_at|date:"DATETIME_FORMAT" }}
- Plaats: {% if location %}{{ location|format_address:"O hlT, P W" }}{% endif %}

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_forwarded_to_external(self):
        md = """Geachte behandelaar,

Er is een melding binnengekomen bij de Gemeente. Kunnen jullie hier naar kijken en ons laten weten of jullie deze kunnen afhandelen.

Wat kunt u doen?
U kunt de melding gelijk inzien en oppakken. Als de melding verwerkt, ontvangen wij graag een bericht.

[Bekijk de actie]({{ reaction_url }})

Nummer: {{ formatted_signal_id }}


Met vriendelijke groet,  

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte behandelaar,

Er is een melding binnengekomen bij de Gemeente. Kunnen jullie hier naar kijken en ons laten weten of jullie deze kunnen afhandelen.

Wat kunt u doen?
U kunt de melding gelijk inzien en oppakken. Als de melding verwerkt, ontvangen wij graag een bericht.

Bekijk de actie {{ reaction_url }}

Nummer: {{ formatted_signal_id }}

Met vriendelijke groet,  

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))
