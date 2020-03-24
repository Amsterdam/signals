from textwrap import dedent

from django.db import migrations, models

from signals.apps.signals.models import Category

# Moved from signals/apps/email_integrations/core/messages.py to make sure the migration keeps working
ALL_AFHANDELING_TEXT = {
    Category.HANDLING_A3DMC: """\
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_A3DEC: """\
Wij handelen uw melding binnen drie werkdagen af. U ontvangt dan geen apart bericht meer.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    Category.HANDLING_A3WMC: """\
We laten u binnen 3 weken weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_A3WEC: """\
Wij handelen uw melding binnen drie weken af. U ontvangt dan geen apart bericht meer.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    Category.HANDLING_I5DMC: """\
Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer uw melding wordt afgehandeld. Dat doen we via e-mail.""",  # noqa E501
    Category.HANDLING_STOPEC: """\
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties handelen wij meestal binnen 5 werkdagen af. U ontvangt dan geen apart bericht meer.
Als we uw melding niet binnen 5 werkdagen kunnen afhandelen, hoort u - via e-mail – hoe wij uw melding oppakken.""",  # noqa E501
    Category.HANDLING_KLOKLICHTZC: """\
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties kunnen wat langer duren. Wij kunnen u hier helaas niet altijd van op de hoogte houden.""",  # noqa E501
    Category.HANDLING_GLADZC: """\
Bij gladheid door sneeuw of bladeren pakken we hoofdwegen en fietsroutes als eerste aan. Andere meldingen behandelen we als de belangrijkste routes zijn gedaan.""",  # noqa E501
    Category.HANDLING_GLAD_OLIE: """\
Gaat het om gladheid door een ongeluk (olie of frituurvet op de weg)? Dan pakken we uw melding zo snel mogelijk op. In ieder geval binnen 3 werkdagen.""",  # noqa E501
    Category.HANDLING_A3DEVOMC: """\
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken. We houden u op de hoogte.""",  # noqa E501
    Category.HANDLING_WS1EC: """\
We geven uw melding door aan de handhavers. Als dat mogelijk is ondernemen zij direct actie, maar zij kunnen niet altijd snel genoeg aanwezig zijn.

Blijf overlast aan ons melden. Ook als we niet altijd direct iets voor u kunnen doen. We gebruiken alle meldingen om overlast in de toekomst te kunnen beperken.""",  # noqa E501
    Category.HANDLING_WS2EC: """\
We geven uw melding door aan onze handhavers. Zij beoordelen of het nodig is direct actie te ondernemen. Bijvoorbeeld omdat er olie lekt of omdat de situatie gevaar oplevert voor andere boten.

Als er geen directe actie nodig is, dan pakken we uw melding op buiten het vaarseizoen (september - maart).

Bekijk in welke situaties we een wrak weghalen. Boten die vol met water staan, maar nog wél drijven, mogen we bijvoorbeeld niet weghalen.""",  # noqa E501
    Category.HANDLING_WS3EC: """\
We geven uw melding door aan onze handhavers. Zij beoordelen of het nodig is direct actie te ondernemen. Bijvoorbeeld omdat er olie lekt of omdat de situatie gevaar oplevert voor andere boten.

Als er geen directe actie nodig is, dan pakken we uw melding op buiten het vaarseizoen (september - maart).
""",  # noqa 501
    Category.HANDLING_REST: """\
Wij bekijken uw melding en zorgen dat het juiste onderdeel van de gemeente deze gaat behandelen. Heeft u contactgegevens achtergelaten? Dan nemen wij bij onduidelijkheid contact met u op.""",  # noqa E501
    Category.HANDLING_OND: """Bedankt voor uw melding. Wij nemen deze mee in ons onderzoek.""",
    Category.HANDLING_EMPTY: '',
    Category.HANDLING_LIGHTING: """Het herstellen van problemen met de openbare verlichting lukt doorgaans binnen 21 werkdagen. Bij gevaarlijke situaties wordt de melding meteen opgepakt.""",  # noqa E501
    Category.HANDLING_TECHNISCHE_STORING: """Technische storingen worden meestal automatisch gemeld en binnen enkele dagen opgelost. Het beantwoorden van vragen kan tot drie weken duren. We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_STOPEC3: """Gevaarlijke situaties pakken wij zo snel mogelijk op. We laten u binnen 3 werkdagen weten wat we hebben gedaan. We houden u op de hoogte via e-mail.""",  # noqa E501

    Category.HANDLING_URGENTE_MELDINGEN: """Wij beoordelen uw melding. Urgente meldingen pakken we zo snel mogelijk op. Overige meldingen handelen we binnen een week af. We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_3WGM: """Wij handelen uw melding binnen drie weken af. U ontvangt dan geen apart bericht meer.""",  # noqa E501
}


def _add_handling_message(apps, schema_editor):
    # SIG-2402
    # Adds the correct text from the ALL_AFHANDELING_TEXT based on the current category.handling
    Category = apps.get_model('signals', 'Category')

    for category in Category.objects.all():
        if category.handling in ALL_AFHANDELING_TEXT:
            category.handling_message = dedent(ALL_AFHANDELING_TEXT[category.handling])
            category.save()


def _set_handling_message_to_none(apps, schema_editor):
    Category = apps.get_model('signals', 'Category')
    Category.objects.update(handling_message=None)


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0101_default_type_and_history_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='handling_message',
            field=models.TextField(blank=True, null=True),
        ),

        # SIG-2402 Adds the correct text from the ALL_AFHANDELING_TEXT based on the current category.handling
        migrations.RunPython(_add_handling_message, _set_handling_message_to_none),
    ]
