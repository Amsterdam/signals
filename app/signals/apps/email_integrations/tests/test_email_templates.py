# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2023 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from typing import Final

from django.conf import settings
from django.core import mail
from django.test import TestCase
from freezegun import freeze_time

from signals.apps.email_integrations.factories import EmailTemplateFactory
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.email_integrations.services import MailService
from signals.apps.feedback.models import Feedback
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory


class TestEmailTemplates(TestCase):
    def setUp(self):
        self.email_template = EmailTemplate.objects.create(
            key=EmailTemplate.SIGNAL_CREATED,
            title='Template title {{ signal_id }}',
            body='# Template title\n Thanks a lot for reporting **{{ signal_id }}** '
                 '{{ text }}\n{{ ORGANIZATION_NAME }}',
        )

    def test_email_template(self):
        self.assertEqual(str(self.email_template), 'Template title {{ signal_id }}')

        signal = SignalFactory.create(reporter__email='test@example.com')

        MailService.status_mail(signal=signal)

        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {signal.id} {signal.text}\n'
                         f'{settings.ORGANIZATION_NAME}', mail.outbox[0].body)

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')
        self.assertIn('<h1>Template title</h1>', body)
        self.assertIn(f'<p>Thanks a lot for reporting <strong>{signal.id}</strong>', body)

    def test_organization_name_contains_quote(self):
        signal = SignalFactory.create(reporter__email='test@example.com')

        with self.settings(ORGANIZATION_NAME='Gemeente \'s-Hertogenbosch'):
            MailService.status_mail(signal=signal)

        self.assertEqual(f'Template title {signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {signal.id} {signal.text}\n'
                         f'Gemeente \'s-Hertogenbosch', mail.outbox[0].body)

    def test_evil_input(self):
        evil_signal = SignalFactory.create(reporter__email='test@example.com',
                                           text='<script>alert("something evil");</script>')

        MailService.status_mail(signal=evil_signal)

        self.assertEqual(f'Template title {evil_signal.id}', mail.outbox[0].subject)
        self.assertEqual(f'Template title\n\nThanks a lot for reporting {evil_signal.id} '
                         f'alert("something evil");\n{settings.ORGANIZATION_NAME}', mail.outbox[0].body)


class TestCompleteTemplates(TestCase):
    TEMPLATES: Final = (
        (
            EmailTemplate.SIGNAL_CREATED,
            """Geachte melder,

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
{% endif %}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD,
            """Geachte melder,
 
Op {{ created_at|date:"j F Y" }} om {{ created_at|date:"H.i" }} uur hebt u een melding gedaan bij de gemeente. In deze mail vertellen wij u wat wij hebben kunnen doen.

**U liet ons het volgende weten**  
{{ text }}

**Wat hebben wij kunnen doen?**  
{{ status_text }}

**Bent u tevreden met de afhandeling van uw melding?**

[![Ja, ik ben tevreden](https://acc.meldingen.amsterdam.nl/assets/images/happy.png) Ja, ik ben tevreden]({{ positive_feedback_url }})

[![Nee, ik ben niet tevreden](https://acc.meldingen.amsterdam.nl/assets/images/unhappy.png) Nee, ik ben niet tevreden]({{ negative_feedback_url }})

**Gegevens van uw melding**  
Nummer: {{ formatted_signal_id }}  
Gemeld op: {{ created_at|date:"j F Y, H.i" }} uur  
Plaats: {% if address %}{{ address|format_address:"O hlT, P W" }}{% else %}Locatie is gepind op de kaart{% endif %}

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: {{ formatted_signal_id }}.

Met vriendelijke groet,

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD_KTO_NEGATIVE_CONTACT,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_STATUS_CHANGED_FORWARD_TO_EXTERNAL,
            """Geachte behandelaar,

Er is een melding binnengekomen bij de Gemeente. Kunnen jullie hier naar kijken en ons laten weten of jullie deze kunnen afhandelen.

Wat kunt u doen?
U kunt de melding gelijk inzien en oppakken. Als de melding verwerkt, ontvangen wij graag een bericht.

[Bekijk de actie]({{ reaction_url }})

Nummer: {{ formatted_signal_id }}


Met vriendelijke groet,  

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_FEEDBACK_RECEIVED,
            """Geachte melder,

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

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.SIGNAL_FORWARD_TO_EXTERNAL_REACTION_RECEIVED,
            """Geachte behandelaar,

Bedankt voor het invullen van het actieformulier. Uw informatie helpt ons bij het verwerken van de melding.

U liet ons het volgende weten:  
{{ reaction_text }}

Gegevens van de melding
- Nummer: {{ formatted_signal_id }}
- Gemeld op: {{ created_at|date:"DATETIME_FORMAT" }}
- Plaats: {% if location %}{{ location|format_address:"O hlT, P W" }}{% endif %}


Met vriendelijke groet,

{{ ORGANIZATION_NAME }}""" # noqa
        ),
        (
            EmailTemplate.MY_SIGNAL_TOKEN,
            """Geachte melder,

[Bevestig uw e-mailadres]({{ my_signals_url }}) om in te loggen op uw meldingenoverzicht. In uw meldingenoverzicht vindt u al uw meldingen van de afgelopen 12 maanden terug. En u ziet status updates.

**Meer weten?**  
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08:00 tot 18:00.


Met vriendelijke groet,

{{ ORGANIZATION_NAME }}

_Dit bericht is automatisch gegenereerd_""" # noqa
        ),
    )

    @classmethod
    def setUpTestData(cls):
        for template in cls.TEMPLATES:
            EmailTemplateFactory.create(key=template[0], body=template[1])

    def test_signal_created(self):
        with freeze_time('2023-07-04 13:37'):
            signal = SignalFactory.create(reporter__email='test@example.com', reporter__phone='0123456789')

        MailService.status_mail(signal=signal)

        assert mail.outbox[0].body == f"""Geachte melder,

Dank voor uw melding. Fijn dat u zich betrokken voelt bij de stad.

Uw melding
{signal.text}

Nummer: SIG-{signal.id}
Gemeld op: 4 juli 2023, 15.37 uur
Plaats: Sesamstraat 666, 1011 AA Ergens

Wat doen we met uw melding?
Test handling message (child category)

Volg zelf uw meldingen online
U kunt nu ook online uw meldingen volgen. Wij doen een proef met de app Yivi. We zoeken enthousiaste Amsterdammers die dit willen uitproberen. Ga naar Meldingen openbare ruimte online volgen https://mijn.amsterdam.nl/inloggen-met-yivi?utm_source=melding-doen-activatie-yivi-inlog&utm_medium=email&utm_campaign=yivi-login&utm_content=link-in-aanmeldingsmail-20230501 om het uit te proberen.

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.

Met vriendelijke groet,

Gemeente Amsterdam

Dit bericht is automatisch gemaakt met de informatie uit uw melding.

U gaf ook nog deze informatie

Vragen 

Uw contactgegevens
Om uw privacy te beschermen hebben wij uw gegevens onherkenbaar gemaakt voor anderen.

Wat is uw telefoonnummer?
*******789

Wat is uw e-mailadres?
t**t@******e.com

Melding doorsturen

Nee, ik geef de gemeente Amsterdam geen toestemming om mijn melding door te sturen naar andere organisaties als de melding niet voor de gemeente is bestemd.""" # noqa

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')

        assert body == f"""
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Uw melding {signal.id}</title>
</head>
<body>
    <p>Geachte melder,</p>
<p>Dank voor uw melding. Fijn dat u zich betrokken voelt bij de stad.</p>
<p><strong>Uw melding</strong><br />
{signal.text}</p>
<p>Nummer: SIG-{signal.id}<br />
Gemeld op: 4 juli 2023, 15.37 uur<br />
Plaats: Sesamstraat 666, 1011 AA Ergens</p>
<p><strong>Wat doen we met uw melding?</strong><br />
Test handling message (child category)</p>
<p><strong>Volg zelf uw meldingen online</strong><br />
U kunt nu ook online uw meldingen volgen. Wij doen een proef met de app Yivi. We zoeken enthousiaste Amsterdammers die dit willen uitproberen. Ga naar <a href="https://mijn.amsterdam.nl/inloggen-met-yivi?utm_source=melding-doen-activatie-yivi-inlog&amp;utm_medium=email&amp;utm_campaign=yivi-login&amp;utm_content=link-in-aanmeldingsmail-20230501">Meldingen openbare ruimte online volgen</a> om het uit te proberen.</p>
<p><strong>Meer weten?</strong><br />
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.</p>
<p>Met vriendelijke groet,</p>
<p>Gemeente Amsterdam</p>
<p><em>Dit bericht is automatisch gemaakt met de informatie uit uw melding.</em></p>
<hr />
<h4>U gaf ook nog deze informatie</h4>
<p><strong>Vragen</strong>  </p>
<p><strong>Uw contactgegevens</strong><br />
Om uw privacy te beschermen hebben wij uw gegevens onherkenbaar gemaakt voor anderen.</p>
<p>Wat is uw telefoonnummer?<br />
*******789</p>
<p>Wat is uw e-mailadres?<br />
t**t@******e.com</p>
<p><strong>Melding doorsturen</strong></p>
<p>Nee, ik geef de gemeente Amsterdam geen toestemming om mijn melding door te sturen naar andere organisaties als de melding niet voor de gemeente is bestemd.</p>
</body>
</html>
""" # noqa

    def test_signal_handled(self):
        with freeze_time('2023-07-04 13:37'):
            signal = SignalFactory.create(
                reporter__email='test@example.com',
                reporter__phone='0123456789',
                status__state=workflow.AFGEHANDELD,
            )

        MailService.status_mail(signal=signal)

        feedback = Feedback.objects.filter(_signal=signal).get()

        assert mail.outbox[0].body == f"""Geachte melder,

Op 4 juli 2023 om 15.37 uur hebt u een melding gedaan bij de gemeente. In deze mail vertellen wij u wat wij hebben kunnen doen.

U liet ons het volgende weten
{signal.text}

Wat hebben wij kunnen doen?
{signal.status.text}

Bent u tevreden met de afhandeling van uw melding?

Ja, ik ben tevreden Ja, ik ben tevreden http://dummy_link/kto/ja/{feedback.token}

Nee, ik ben niet tevreden Nee, ik ben niet tevreden http://dummy_link/kto/nee/{feedback.token}

Gegevens van uw melding
Nummer: SIG-{signal.id}
Gemeld op: 4 juli 2023, 15.37 uur
Plaats: Sesamstraat 666, 1011 AA Ergens

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.

Met vriendelijke groet,

Gemeente Amsterdam""" # noqa

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')

        assert body == f"""
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Uw melding {signal.id}</title>
</head>
<body>
    <p>Geachte melder,</p>
<p>Op 4 juli 2023 om 15.37 uur hebt u een melding gedaan bij de gemeente. In deze mail vertellen wij u wat wij hebben kunnen doen.</p>
<p><strong>U liet ons het volgende weten</strong><br />
{signal.text}</p>
<p><strong>Wat hebben wij kunnen doen?</strong><br />
{signal.status.text}</p>
<p><strong>Bent u tevreden met de afhandeling van uw melding?</strong></p>
<p><a href="http://dummy_link/kto/ja/{feedback.token}"><img alt="Ja, ik ben tevreden" src="https://acc.meldingen.amsterdam.nl/assets/images/happy.png" /> Ja, ik ben tevreden</a></p>
<p><a href="http://dummy_link/kto/nee/{feedback.token}"><img alt="Nee, ik ben niet tevreden" src="https://acc.meldingen.amsterdam.nl/assets/images/unhappy.png" /> Nee, ik ben niet tevreden</a></p>
<p><strong>Gegevens van uw melding</strong><br />
Nummer: SIG-{signal.id}<br />
Gemeld op: 4 juli 2023, 15.37 uur<br />
Plaats: Sesamstraat 666, 1011 AA Ergens</p>
<p><strong>Meer weten?</strong><br />
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.</p>
<p>Met vriendelijke groet,</p>
<p>Gemeente Amsterdam</p>
</body>
</html>
""" # noqa

    def test_signal_scheduled(self):
        with freeze_time('2023-07-04 13:37'):
            signal = SignalFactory.create(
                reporter__email='test@example.com',
                reporter__phone='0123456789',
                status__state=workflow.INGEPLAND,
                status__send_email=True,
            )

        MailService.status_mail(signal=signal)

        assert mail.outbox[0].body == f"""Geachte melder,

Op 4 juli 2023 om 15.37 uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u meer over wat wij aan het doen zijn.

U liet ons het volgende weten
{signal.text}

Meer informatie
{signal.status.text}

Gegevens van uw melding
Nummer: SIG-{signal.id}
Gemeld op: 4 juli 2023, 15.37 uur
Plaats: Sesamstraat 666, 1011 AA Ergens

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.

Met vriendelijke groet,

Gemeente Amsterdam""" # noqa

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')

        assert body == f"""
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Uw melding {signal.id}</title>
</head>
<body>
    <p>Geachte melder,</p>
<p>Op 4 juli 2023 om 15.37 uur hebt u een melding gedaan bij de gemeente. In deze e-mail leest u meer over wat wij aan het doen zijn.</p>
<p><strong>U liet ons het volgende weten</strong><br />
{signal.text}</p>
<p><strong>Meer informatie</strong><br />
{signal.status.text}</p>
<p><strong>Gegevens van uw melding</strong><br />
Nummer: SIG-{signal.id}<br />
Gemeld op: 4 juli 2023, 15.37 uur<br />
Plaats: Sesamstraat 666, 1011 AA Ergens</p>
<p><strong>Meer weten?</strong><br />
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.</p>
<p>Met vriendelijke groet,</p>
<p>Gemeente Amsterdam</p>
</body>
</html>
""" # noqa

    def test_signal_reopened(self):
        with freeze_time('2023-07-04 13:37'):
            signal = SignalFactory.create(
                reporter__email='test@example.com',
                reporter__phone='0123456789',
                status__state=workflow.HEROPEND,
            )

        MailService.status_mail(signal=signal)

        assert mail.outbox[0].body == f"""Geachte melder,

U bent niet tevreden over wat wij met uw melding hebben gedaan. Dat spijt ons. Wij gaan opnieuw aan het werk.

Wat wij nu gaan doen
{signal.status.text}

U liet ons het volgende weten
Bent u tevreden met de afhandeling van uw melding?
Nee, Ik ben niet tevreden met de afhandeling van mijn melding

Waarom bent u niet tevreden?

Gegevens van uw melding
Nummer: SIG-{signal.id}
Gemeld op: 4 juli 2023, 15.37 uur
Plaats: Sesamstraat 666, 1011 AA Ergens

Meer weten?
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.

Met vriendelijke groet,

Gemeente Amsterdam""" # noqa

        body, mime_type = mail.outbox[0].alternatives[0]
        self.assertEqual(mime_type, 'text/html')

        assert body == f"""
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Uw melding {signal.id}</title>
</head>
<body>
    <p>Geachte melder,</p>
<p>U bent niet tevreden over wat wij met uw melding hebben gedaan. Dat spijt ons. Wij gaan opnieuw aan het werk.</p>
<p><strong>Wat wij nu gaan doen</strong><br />
{signal.status.text}</p>
<p><strong>U liet ons het volgende weten</strong><br />
Bent u tevreden met de afhandeling van uw melding?<br />
<em>Nee, Ik ben niet tevreden met de afhandeling van mijn melding</em></p>
<p><strong>Waarom bent u niet tevreden?</strong></p>
<p><strong>Gegevens van uw melding</strong><br />
Nummer: SIG-{signal.id}<br />
Gemeld op: 4 juli 2023, 15.37 uur<br />
Plaats: Sesamstraat 666, 1011 AA Ergens</p>
<p><strong>Meer weten?</strong><br />
Voor vragen over uw melding kunt u bellen met telefoonnummer 14 020, maandag tot en met vrijdag van 08.00 tot 18.00. Geef dan ook het nummer van uw melding door: SIG-{signal.id}.</p>
<p>Met vriendelijke groet,</p>
<p>Gemeente Amsterdam</p>
</body>
</html>
""" # noqa
