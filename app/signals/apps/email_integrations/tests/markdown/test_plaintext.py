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

    def test_feedback_received(self):
        md = """Geachte melder,

Bedankt voor uw reactie. U hoort binnen 3 werkdagen weer bericht van ons.  

**Bent u tevreden met de afhandeling van uw melding?**  
{% if feedback_is_satisfied %} Ja, ik ben tevreden met de afhandeling van mijn melding {% else%} Nee, Ik ben niet tevreden met de afhandeling van mijn melding {% endif %}  

{% if feedback_is_satisfied %}**Waarom bent u tevreden?** {% else %} **Waarom bent u niet tevreden?** {% endif %}  
{% if feedback_text %} {{ feedback_text }}{% else %}{% for f_text in feedback_text_list %}{{ f_text }}{% endfor %}
{%endif %}

{% if feedback_text_extra %}
**Wilt u ons verder nog iets laten weten?**  
{{ feedback_text_extra }}
{% endif %}

**Contact**  
{% if feedback_allows_contact %} Ja, bel of e-mail mij over deze melding of over mijn reactie. {% else %} Nee, bel of e-mail mij niet meer over deze melding of over mijn reactie. {% endif %}

**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}  

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte melder,

Bedankt voor uw reactie. U hoort binnen 3 werkdagen weer bericht van ons.  

Bent u tevreden met de afhandeling van uw melding?
{% if feedback_is_satisfied %} Ja, ik ben tevreden met de afhandeling van mijn melding {% else%} Nee, Ik ben niet tevreden met de afhandeling van mijn melding {% endif %}

{% if feedback_is_satisfied %}Waarom bent u tevreden? {% else %} Waarom bent u niet tevreden? {% endif %}
{% if feedback_text %} {{ feedback_text }}{% else %}{% for f_text in feedback_text_list %}{{ f_text }}{% endfor %}
{%endif %}

{% if feedback_text_extra %}
Wilt u ons verder nog iets laten weten?
{{ feedback_text_extra }}
{% endif %}

Contact
{% if feedback_allows_contact %} Ja, bel of e-mail mij over deze melding of over mijn reactie. {% else %} Nee, bel of e-mail mij niet meer over deze melding of over mijn reactie. {% endif %}

Gegevens van uw melding
Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))
