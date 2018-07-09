# TODO In a future version this should be in the database

# Constants for afhandeling
A3DMC = 'A3DMC'
A3DEC = 'A3DEC'
A3WMC = 'A3WMC'
A3WEC = 'A3WEC'
I5DMC = 'I5DMC'
STOPEC = 'STOPEC'
KLOKLICHTZC = 'KLOKLICHTZC'
GLADZC = 'GLADZC'
A3DEVOMC = 'A3DEVOMC'
WS1EC = 'WS1EC'
WS2EC = 'WS2EC'
REST = 'REST'

ALL_SUB_CATEGORIES = (
    # sub_code, categorie, sub_categorie, afhandeling
    ('F01', 'Afval', 'Veeg-/zwerfvuil', A3DEC),
    ('F02', 'Afval', 'Grofvuil', A3DEVOMC),
    ('F03', 'Afval', 'Huisafval', A3DMC),
    ('F04', 'Afval', 'Bedrijfsafval', A3DMC),
    ('F05', 'Afval', 'Puin/sloopafval', A3DMC),
    ('F06', 'Afval', 'Container vol', A3DMC),
    ('F07', 'Afval', 'Prullenbak vol', A3DEC),
    ('F08', 'Afval', 'Container kapot', A3DMC),
    ('F09', 'Afval', 'Prullenbak kapot', A3DMC),
    ('F10', 'Afval', 'Asbest/accu', A3DMC),
    ('F11', 'Afval', 'Overig afval', I5DMC),
    ('F12', 'Afval', 'Container plastic afval vol', A3DMC),
    ('F13', 'Afval', 'Container plastic afval kapot', A3DMC),
    ('F14', 'Wegen/verkeer/straatmeubilair', 'Onderhoud stoep/straat/fietspad', A3DEC),
    ('F15', 'Wegen/verkeer/straatmeubilair', 'Verkeersbord/verkeersafzetting', A3DEC),
    ('F16', 'Wegen/verkeer/straatmeubilair', 'Gladheid', GLADZC),
    ('F17', 'Wegen/verkeer/straatmeubilair', 'Omleiding/belijning verkeer', A3WEC),
    ('F18', 'Wegen/verkeer/straatmeubilair', 'Brug', A3WEC),
    ('F19', 'Wegen/verkeer/straatmeubilair', 'Straatmeubilair', I5DMC),
    ('F20', 'Wegen/verkeer/straatmeubilair', 'Fietsenrek/nietje', I5DMC),
    ('F21', 'Wegen/verkeer/straatmeubilair', 'Put/riolering verstopt', I5DMC),
    ('F22', 'Wegen/verkeer/straatmeubilair', 'Speelplaats', I5DMC),
    ('F23', 'Wegen/verkeer/straatmeubilair', 'Sportvoorziening', I5DMC),
    ('F24a', 'Wegen/verkeer/straatmeubilair', 'Straatverlichting', KLOKLICHTZC),
    ('F24b', 'Wegen/verkeer/straatmeubilair', 'Klok', KLOKLICHTZC),
    ('F25', 'Wegen/verkeer/straatmeubilair', 'Stoplicht', STOPEC),
    ('F26', 'Wegen/verkeer/straatmeubilair', 'Overig wegen/verkeer/straatmeubilair', I5DMC),
    ('F27', 'Wegen/verkeer/straatmeubilair', 'Verkeersoverlast/verkeerssituaties', I5DMC),
    ('F28', 'Openbare ruimte', 'Lozing/dumping /bodemverontreiniging', A3DMC),
    ('F29', 'Openbare ruimte', 'Parkeeroverlast', A3DMC),
    ('F30', 'Openbare ruimte', 'Fietswrak', A3WMC),
    ('F31', 'Openbare ruimte', 'Stank-/geluid', A3WMC),
    ('F32', 'Openbare ruimte', 'Bouw-/sloopoverlast', A3WMC),
    ('F33', 'Openbare ruimte', 'Auto-/scooter-/bromfietswrak', A3WMC),
    ('F34', 'Openbare ruimte', 'Graffiti/wildplak', I5DMC),
    ('F35', 'Openbare ruimte', 'Honden(poep)', A3WMC),
    ('F36', 'Openbare ruimte', 'Hinderlijk geplaatst object', I5DMC),
    # vervallen ('F37','Openbare ruimte','Overlast van dieren (bijv. ratten)', 'REST'),
    # vervallen ('F38','Openbare ruimte','Vuurwerkoverlast', 'REST'),
    ('F39', 'Openbare ruimte', 'Deelfiets', A3WMC),
    ('F40', 'Openbare ruimte', 'Overig openbare ruimte', I5DMC),
    ('F41', 'Groen en water', 'Boom', I5DMC),
    ('F42', 'Groen en water', 'Maaien/snoeien', I5DMC),
    ('F43', 'Groen en water', 'Onkruid', I5DMC),
    ('F44', 'Groen en water', 'Drijfvuil', I5DMC),
    ('F45', 'Groen en water', 'Oever/kade/steiger', I5DMC),
    ('F46', 'Groen en water', 'Overig groen en water', I5DMC),
    # vervallen ('F47','Dieren','Hondenpoep', 'REST'),
    ('F48', 'Dieren', 'Ratten', I5DMC),
    ('F49', 'Dieren', 'Ganzen', I5DMC),
    ('F50', 'Dieren', 'Duiven', I5DMC),
    ('F51', 'Dieren', 'Meeuwen', I5DMC),
    ('F52', 'Dieren', 'Wespen', I5DMC),
    ('F53', 'Dieren', 'Dode dieren', A3DMC),
    ('F54', 'Dieren', 'Overig dieren', I5DMC),
    ('F55', 'Personen/groepen', 'Vuurwerk', A3DMC),
    ('F56', 'Personen/groepen', 'Overig personen/groepen', A3DMC),
    ('F57', 'Personen/groepen', 'Personen op het water', A3DMC),
    ('F58', 'Personen/groepen', 'Taxi/bus/fietstaxi', A3DMC),
    ('F59', 'Personen/groepen', 'Jongeren', A3DMC),
    ('F60', 'Personen/groepen', 'Dakloze/bedelen', A3DMC),
    ('F61', 'Personen/groepen', 'Wildplassen/poepen/overgeven', A3DMC),
    ('F62', 'Personen/groepen', 'Drank/drugs', A3DMC),
    ('F63', 'Horeca/bedrijven', 'Muziek horeca/bedrijven', I5DMC),
    ('F64', 'Horeca/bedrijven', 'Installaties', I5DMC),
    ('F65', 'Horeca/bedrijven', 'Terras', I5DMC),
    ('F66', 'Horeca/bedrijven', 'Stank horeca/bedrijven', I5DMC),
    ('F67', 'Horeca/bedrijven', 'Bezoekers (niet op terras)', I5DMC),
    ('F68', 'Horeca/bedrijven', 'Overig horeca/bedrijven', I5DMC),
    ('F69', 'Boten', 'Snel varen', WS1EC),
    ('F70', 'Boten', 'Geluid boten', WS1EC),
    ('F71', 'Boten', 'Gezonken', WS2EC),
    ('F72', 'Boten', 'Overig boten', WS1EC),
    ('F73', 'Overig', 'Overig', REST)
)

SUB_CATEGORIES_DICT = {}
for entry in ALL_SUB_CATEGORIES:
    SUB_CATEGORIES_DICT[entry[2]] = entry

ALL_AFHANDELING_TEXT = {
    A3DMC: """
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",
    A3DEC: """
Wij handelen uw melding binnen 3 werkdagen af. U ontvangt dan geen apart bericht meer.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    A3WMC: """
We laten u binnen 3 weken weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",
    A3WEC: """
Wij handelen uw melding binnen drie weken af. U ontvangt dan geen apart bericht meer.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    I5DMC: """
Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer uw melding wordt afgehandeld. Dat doen we via e-mail.""",
    STOPEC: """
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties handelen wij meestal binnen 5 werkdagen af. U ontvangt dan geen apart bericht meer.
Als we uw melding niet binnen 5 werkdagen kunnen afhandelen, hoort u - via e-mail – hoe wij uw melding oppakken.""",
    KLOKLICHTZC: """
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties kunnen wat langer duren. Wij kunnen u hier helaas niet van  op de hoogte houden.""",
    GLADZC: """
Gaat het om gladheid door een ongeluk (olie of frituurvet op de weg)? Dan pakken we uw melding zo snel mogelijk op. In ieder geval binnen 3 werkdagen.

Bij gladheid door sneeuw of bladeren pakken we hoofdwegen en fietsroutes als eerste aan. Andere meldingen behandelen we als de belangrijkste routes zijn gedaan.

U ontvangt geen apart bericht meer over de afhandeling van uw melding.""",
    A3DEVOMC: """
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.  In Nieuw-West komen we de volgende ophaaldag.
We houden u op de hoogte via e-mail.""",
    WS1EC: """
We geven uw melding door aan onze handhavers. Als dat mogelijk is ondernemen we direct actie. Maar we kunnen niet altijd snel genoeg aanwezig zijn.

Blijf overlast aan ons melden. Ook als we niet altijd direct iets voor u kunnen doen. We gebruiken alle meldingen om overlast in de toekomst te kunnen beperken.""",
    WS2EC: """
We geven uw melding door aan onze handhavers. Zij beoordelen of het nodig en mogelijk is direct actie te ondernemen. Bijvoorbeeld omdat er olie lekt of omdat de situatie gevaar oplevert voor andere boten.

Als er geen directe actie nodig is, dan pakken we uw melding op buiten het vaarseizoen (september - maart).
Bekijk in welke situaties we een wrak weghalen. Boten die vol met water staan, maar nog wél drijven, mogen we bijvoorbeeld niet weghalen.""",
    REST: """
Het is ons helaas niet goed duidelijk wat u bedoelt. We nemen contact met u op.""",
}


def get_afhandeling_text(sub_categorie):
    afhandeling_code = SUB_CATEGORIES_DICT.get(sub_categorie) or REST
    return ALL_AFHANDELING_TEXT[afhandeling_code[3]]

