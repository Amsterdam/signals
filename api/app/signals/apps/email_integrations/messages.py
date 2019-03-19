"""
Category "afhandeling teksten"
"""
from signals.apps.signals.models import Category

# TODO, Move these text to the database and create a helper method on `Category` to get this text
ALL_AFHANDELING_TEXT = {
    Category.HANDLING_A3DMC: """
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_A3DEC: """
Wij handelen uw melding binnen 3 werkdagen af.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    Category.HANDLING_A3WMC: """
We laten u binnen 3 weken weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_A3WEC: """
Wij handelen uw melding binnen drie weken af.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    Category.HANDLING_I5DMC: """
Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer uw melding wordt afgehandeld. Dat doen we via e-mail.""",  # noqa E501
    Category.HANDLING_STOPEC: """
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties handelen wij meestal binnen 5 werkdagen af.
Als we uw melding niet binnen 5 werkdagen kunnen afhandelen, hoort u - via e-mail – hoe wij uw melding oppakken.""",  # noqa E501
    Category.HANDLING_KLOKLICHTZC: """
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties kunnen wat langer duren. Wij kunnen u hier helaas niet altijd van op de hoogte houden.""",  # noqa E501
    Category.HANDLING_GLADZC: """
Gaat het om gladheid door een ongeluk (olie of frituurvet op de weg)? Dan pakken we uw melding zo snel mogelijk op. In ieder geval binnen 3 werkdagen.

Bij gladheid door sneeuw of bladeren pakken we hoofdwegen en fietsroutes als eerste aan. Andere meldingen behandelen we als de belangrijkste routes zijn gedaan.

U ontvangt geen apart bericht meer over de afhandeling van uw melding.""",  # noqa E501
    Category.HANDLING_A3DEVOMC: """
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.  In Nieuw-West komen we de volgende ophaaldag.
We houden u op de hoogte via e-mail.""",  # noqa E501
    Category.HANDLING_WS1EC: """
We geven uw melding door aan onze handhavers. Als dat mogelijk is ondernemen we direct actie. Maar we kunnen niet altijd snel genoeg aanwezig zijn.

Blijf overlast aan ons melden. Ook als we niet altijd direct iets voor u kunnen doen. We gebruiken alle meldingen om overlast in de toekomst te kunnen beperken.""",  # noqa E501
    Category.HANDLING_WS2EC: """
We geven uw melding door aan onze handhavers. Zij beoordelen of het nodig en mogelijk is direct actie te ondernemen. Bijvoorbeeld omdat er olie lekt of omdat de situatie gevaar oplevert voor andere boten.

Als er geen directe actie nodig is, dan pakken we uw melding op buiten het vaarseizoen (september - maart).
Bekijk in welke situaties we een wrak weghalen. Boten die vol met water staan, maar nog wél drijven, mogen we bijvoorbeeld niet weghalen.""",  # noqa E501
    Category.HANDLING_REST: """
Wij bekijken uw melding en zorgen dat het juiste onderdeel van de gemeente deze gaat behandelen. Heeft u contactgegevens achtergelaten? Dan nemen wij bij onduidelijkheid contact met u op.""",  # noqa E501
}
