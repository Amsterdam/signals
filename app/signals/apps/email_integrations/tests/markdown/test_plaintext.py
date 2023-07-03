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

    def test_negative_kto_contact(self):
        md = """Geachte melder,
U bent niet tevreden over wat wij met uw melding hebben gedaan. Dat spijt ons. Wij willen u graag wat meer informatie geven.

**Wat wij u nog meer willen laten weten**  
{{ status_text }}

**U liet ons het volgende weten**  
Bent u tevreden met de afhandeling van uw melding?  
{% if feedback_is_satisfied %} Ja, ik ben tevreden met de afhandeling van mijn melding {% else %} Nee, ik ben niet tevreden met de afhandeling van mijn melding {% endif %}


**Waarom bent u niet tevreden?**  
{% if feedback_text %}{{ feedback_text }}  
{% else %}
{% for f_text in feedback_text_list %}{{ f_text }}  {% endfor %}
{%endif %}
{{ feedback_text_extra }}


**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte melder,
U bent niet tevreden over wat wij met uw melding hebben gedaan. Dat spijt ons. Wij willen u graag wat meer informatie geven.

Wat wij u nog meer willen laten weten
{{ status_text }}

U liet ons het volgende weten
Bent u tevreden met de afhandeling van uw melding?
{% if feedback_is_satisfied %} Ja, ik ben tevreden met de afhandeling van mijn melding {% else %} Nee, ik ben niet tevreden met de afhandeling van mijn melding {% endif %}

Waarom bent u niet tevreden?
{% if feedback_text %}{{ feedback_text }}
{% else %}
{% for f_text in feedback_text_list %}{{ f_text }}  {% endfor %}
{%endif %}
{{ feedback_text_extra }}

Gegevens van uw melding
Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_my_signals_token_requested(self):
        md = """Geachte melder,

[Bevestig uw e-mailadres]({{ my_signals_url }}) om in te loggen op uw meldingenoverzicht. In uw meldingenoverzicht vindt u al uw meldingen van de afgelopen 12 maanden terug. En u ziet status updates.

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00.


Met vriendelijke groet,

{{ ORGANIZATION_NAME }}

_Dit bericht is automatisch gegenereerd_"""
        expected = """Geachte melder,

Bevestig uw e-mailadres {{ my_signals_url }} om in te loggen op uw meldingenoverzicht. In uw meldingenoverzicht vindt u al uw meldingen van de afgelopen 12 maanden terug. En u ziet status updates.

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}

Dit bericht is automatisch gegenereerd"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_reaction_requested_received(self):
        md = """Geachte melder,

Bedankt voor uw reactie. U krijgt binnen 3 werkdagen weer bericht van ons.

**Bent u tevreden met de afhandeling van uw melding?**  
{% if feedback_is_satisfied %} Ja, ik ben tevreden met de afhandeling van mijn melding {% else%} Nee, Ik ben niet tevreden met de afhandeling van mijn melding {% endif %}

{% if feedback_is_satisfied %}**Waarom bent u tevreden?** {% else %} **Waarom bent u niet tevreden?** {% endif %}  
{% if feedback_text %} {{ feedback_text }} {% else %}{% for f_text in feedback_text_list %} {{ f_text }}{% endfor %}
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

Bedankt voor uw reactie. U krijgt binnen 3 werkdagen weer bericht van ons.

Bent u tevreden met de afhandeling van uw melding?
{% if feedback_is_satisfied %} Ja, ik ben tevreden met de afhandeling van mijn melding {% else%} Nee, Ik ben niet tevreden met de afhandeling van mijn melding {% endif %}

{% if feedback_is_satisfied %}Waarom bent u tevreden? {% else %} Waarom bent u niet tevreden? {% endif %}
{% if feedback_text %} {{ feedback_text }} {% else %}{% for f_text in feedback_text_list %} {{ f_text }}{% endfor %}
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

    def test_reaction_requested(self):
        md = """Geachte melder,

Op {{ created_at|date:"j F Y" }} hebt u een melding gedaan bij de gemeente. Wij hebben meer informatie nodig. Wilt u alstublieft binnen 5 dagen onze vragen beantwoorden?  
[Beantwoord de vragen]({{ reaction_url }})

**U liet ons het volgende weten**  
{{text}}

**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte melder,

Op {{ created_at|date:"j F Y" }} hebt u een melding gedaan bij de gemeente. Wij hebben meer informatie nodig. Wilt u alstublieft binnen 5 dagen onze vragen beantwoorden?
Beantwoord de vragen {{ reaction_url }}

U liet ons het volgende weten
{{text}}

Gegevens van uw melding
Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_optional(self):
        md = """Geachte melder,

Op {{ created_at|date:"j F Y" }} om {{ created_at|date:"H.i" }} uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u de stand van zaken van uw melding.

**U liet ons het volgende weten**  
{{ text }}

**Stand van zaken**  
{{ status_text }}

**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte melder,

Op {{ created_at|date:"j F Y" }} om {{ created_at|date:"H.i" }} uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u de stand van zaken van uw melding.

U liet ons het volgende weten
{{ text }}

Stand van zaken
{{ status_text }}

Gegevens van uw melding
Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_signal_reopened(self):
        md = """Geachte melder,

U bent niet tevreden over wat wij met uw melding hebben gedaan. Dat spijt ons. Wij gaan opnieuw aan het werk.

**Wat wij nu gaan doen**  
{{ status_text }}

**U liet ons het volgende weten**  
Bent u tevreden met de afhandeling van uw melding?  
{% if feedback_is_satisfied %}*Ja, ik ben tevreden met de afhandeling van mijn melding*{% else%}*Nee, Ik ben niet tevreden met de afhandeling van mijn melding*{% endif %}

{% if feedback_is_satisfied %}**Waarom bent u tevreden?**{% else %}**Waarom bent u niet tevreden?**{% endif %}
{% if feedback_text %}
*{{ feedback_text }}*  
{% else %}
{% for f_text in feedback_text_list %}  *{{ f_text }}*  
{% endfor %}
{% endif %}

{% if feedback_text_extra %}
**Wilt u ons verder nog iets laten weten?**  
*{{ feedback_text_extra }}*
{% endif %}

**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte melder,

U bent niet tevreden over wat wij met uw melding hebben gedaan. Dat spijt ons. Wij gaan opnieuw aan het werk.

Wat wij nu gaan doen
{{ status_text }}

U liet ons het volgende weten
Bent u tevreden met de afhandeling van uw melding?
{% if feedback_is_satisfied %}Ja, ik ben tevreden met de afhandeling van mijn melding{% else%}Nee, Ik ben niet tevreden met de afhandeling van mijn melding{% endif %}

{% if feedback_is_satisfied %}Waarom bent u tevreden?{% else %}Waarom bent u niet tevreden?{% endif %}
{% if feedback_text %}
{{ feedback_text }}
{% else %}
{% for f_text in feedback_text_list %}  {{ f_text }}
{% endfor %}
{% endif %}

{% if feedback_text_extra %}
Wilt u ons verder nog iets laten weten?
{{ feedback_text_extra }}
{% endif %}

Gegevens van uw melding
Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_signal_scheduled(self):
        md = """Geachte melder,

Op {{ created_at|date:"j F Y" }} om {{ created_at|date:"H.i" }} uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u meer over wat wij aan het doen zijn.

**U liet ons het volgende weten**  
{{ text }}

**Meer informatie**  
{{ status_text }}

**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""
        expected = """Geachte melder,

Op {{ created_at|date:"j F Y" }} om {{ created_at|date:"H.i" }} uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u meer over wat wij aan het doen zijn.

U liet ons het volgende weten
{{ text }}

Meer informatie
{{ status_text }}

Gegevens van uw melding
Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}"""

        assert expected == strip_markdown_html(markdown.markdown(md))

    def test_signal_created(self):
        md = """Geachte melder,

Dank voor uw melding. Fijn dat u zich betrokken voelt bij de stad.

**Uw melding**  
{{ text }}
 
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Wat doen we met uw melding?**  
{{ handling_message }}

**Volg zelf uw meldingen online**  
U kunt nu ook online uw meldingen volgen. Wij doen een proef met de app Yivi. We zoeken enthousiaste Amsterdammers die dit willen uitproberen. Ga naar [Meldingen openbare ruimte online volgen](https://mijn.amsterdam.nl/inloggen-met-yivi?utm_source=melding-doen-activatie-yivi-inlog&utm_medium=email&utm_campaign=yivi-login&utm_content=link-in-aanmeldingsmail-20230501) om het uit te proberen.

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}

*Dit bericht is automatisch gemaakt met de informatie uit uw melding.*

____________________________________________________________________________________________________

#### U gaf ook nog deze informatie

**Vragen**  
{% for label, answers in extra_properties.items %}{{ label }}  
*{% for answer in answers %}{{ answer}}{% if not forloop.last %}, {% endif %}{% endfor %}*  
{% endfor %}
 
**Uw contactgegevens**  
Om uw privacy te beschermen hebben wij uw gegevens onherkenbaar gemaakt voor anderen.
{% if reporter_phone %}
Wat is uw telefoonnummer?  
{{ reporter_phone}}
{% endif %}{% if reporter_email %}
Wat is uw e-mailadres?  
{{ reporter_email}}  
{% endif %}

**Melding doorsturen**  
{% if reporter_sharing_allowed %}
Ja, ik geef de gemeente Amsterdam toestemming om mijn melding door te sturen naar andere organisaties als de melding niet voor de gemeente is bestemd.
{% else %}
Nee, ik geef de gemeente Amsterdam geen toestemming om mijn melding door te sturen naar andere organisaties als de melding niet voor de gemeente is bestemd.
{% endif %}"""
        expected = """Geachte melder,

Dank voor uw melding. Fijn dat u zich betrokken voelt bij de stad.

Uw melding
{{ text }}

Nummer: {{ formatted_signal_id }}
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

Wat doen we met uw melding?
{{ handling_message }}

Volg zelf uw meldingen online
U kunt nu ook online uw meldingen volgen. Wij doen een proef met de app Yivi. We zoeken enthousiaste Amsterdammers die dit willen uitproberen. Ga naar Meldingen openbare ruimte online volgen https://mijn.amsterdam.nl/inloggen-met-yivi?utm_source=melding-doen-activatie-yivi-inlog&utm_medium=email&utm_campaign=yivi-login&utm_content=link-in-aanmeldingsmail-20230501 om het uit te proberen.

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}

Dit bericht is automatisch gemaakt met de informatie uit uw melding.

U gaf ook nog deze informatie

Vragen
{% for label, answers in extra_properties.items %}{{ label }}
{% for answer in answers %}{{ answer}}{% if not forloop.last %}, {% endif %}{% endfor %}
{% endfor %}

Uw contactgegevens
Om uw privacy te beschermen hebben wij uw gegevens onherkenbaar gemaakt voor anderen.
{% if reporter_phone %}
Wat is uw telefoonnummer?
{{ reporter_phone}}
{% endif %}{% if reporter_email %}
Wat is uw e-mailadres?
{{ reporter_email}}
{% endif %}

Melding doorsturen
{% if reporter_sharing_allowed %}
Ja, ik geef de gemeente Amsterdam toestemming om mijn melding door te sturen naar andere organisaties als de melding niet voor de gemeente is bestemd.
{% else %}
Nee, ik geef de gemeente Amsterdam geen toestemming om mijn melding door te sturen naar andere organisaties als de melding niet voor de gemeente is bestemd.
{% endif %}"""

        html = markdown.markdown(md)
        print(html)

        assert expected == strip_markdown_html(html)
