# TODO In a future version this should be in the database

# Afdeling/Diensten
# Zie : https://dokuwiki.datapunt.amsterdam.nl/doku.php?id=start:toepassingen:signalen:ontwerp:referentietabellen:dienstenvsrubrieken

# Code, Naam, Intern/Extern
ALL_DEPARTMENTS = {
    "POA" : ("Port of Amsterdam", "E"),
    "THO": ("THOR", "I"),
    "WAT": ("Waternet", "E"),
    "STW": ("Stadswerken", "I"),
    "AEG": ("Afval en Grondstoffen", "I"),
    "ASC": ("Actie Service Centrum","I" ),
    "POL": ("Politie", "E"),
    "GGD": ("GGD", "E"),
    # "VOR": ("V&OR", "I"),  # Onderscheid V&OR OVL en V&OR VRI ???
    "OVL": ("V&OR OVL", "I"),  # Onderscheid V&OR OVL en V&OR VRI ???
    "VRI": ("V&OR VRI", "I"),  # Onderscheid V&OR OVL en V&OR VRI ???
    "CCA": ("CCA", "I"),
    "STL": ("Stadsloket", "I"),
    "OMG": ("Omgevingsdienst", "I"), # Intern/extern ???
    "VTH": ("VTH", "I"), # Wat is VTH ? Intern/Extern ?
    "FB": ("FB", "I"), # ?? what is FB
}

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
    # sub_code, categorie, sub_categorie, afhandeling, afdelingen
    ('F01', 'Afval', 'Veeg- / zwerfvuil', A3DEC, "CCA,ASC,STW"),
    ('F02', 'Afval', 'Grofvuil', A3DEVOMC, "CCA,ASC,AEG"),
    ('F03', 'Afval', 'Huisafval', A3DMC, "CCA,ASC,AEG"),
    ('F04', 'Afval', 'Bedrijfsafval', A3DMC, "CCA,ASC,AEG"),
    ('F05', 'Afval', 'Puin / sloopafval', A3DMC, "CCA,ASC,AEG"),
    ('F06', 'Afval', 'Container is vol', A3DMC, "CCA,ASC,AEG"),
    ('F07', 'Afval', 'Prullenbak is vol', A3DEC, "CCA,ASC,STW"),
    ('F08', 'Afval', 'Container is kapot', A3DMC, "CCA,ASC,AEG"),
    ('F09', 'Afval', 'Prullenbak is kapot', A3DMC, "CCA,ASC,STW"),
    ('F10', 'Afval', 'Asbest / accu', A3DMC, "CCA,ASC,AEG"),
    ('F11', 'Afval', 'Overig afval', I5DMC, "CCA,ASC,STW,AEG"),
    ('F12', 'Afval', 'Container voor plastic afval is vol', A3DMC, "CCA,ASC,AEG"),
    ('F13', 'Afval', 'Container voor plastic afval is kapot', A3DMC, "CCA,ASC,AEG"),
    ('F14', 'Wegen, verkeer, straatmeubilair', 'Onderhoud stoep, straat en fietspad', A3DEC, "CCA,ASC,STW"),
    ('F15', 'Wegen, verkeer, straatmeubilair', 'Verkeersbord, verkeersafzetting', A3DEC, "CCA,ASC,STW"),
    ('F16', 'Wegen, verkeer, straatmeubilair', 'Gladheid', GLADZC, "CCA,ASC,STW"),
    ('F17', 'Wegen, verkeer, straatmeubilair', 'Omleiding / belijning verkeer', A3WEC, "CCA,ASC,STW"),
    ('F18', 'Wegen, verkeer, straatmeubilair', 'Brug', A3WEC, "CCA,ASC,STW"),
    ('F19', 'Wegen, verkeer, straatmeubilair', 'Straatmeubilair', I5DMC, "CCA,ASC,STW"),
    ('F20', 'Wegen, verkeer, straatmeubilair', 'Fietsrek / nietje', I5DMC, "CCA,ASC,STW"),
    ('F21', 'Wegen, verkeer, straatmeubilair', 'Put / riolering verstopt', I5DMC, "CCA,ASC,STW"),
    ('F22', 'Wegen, verkeer, straatmeubilair', 'Speelplaats', I5DMC, "CCA,ASC,STW"),
    ('F23', 'Wegen, verkeer, straatmeubilair', 'Sportvoorziening', I5DMC, "CCA,ASC,STW"),
    ('F24a', 'Wegen, verkeer, straatmeubilair', 'Straatverlichting / openbare klok', KLOKLICHTZC, "CCA,ASC"),
    ('F24b', 'Wegen, verkeer, straatmeubilair', 'Klok', KLOKLICHTZC, "CCA,ASC,OVL"),  # TODO: not in meldingen classificatie
    ('F25', 'Wegen, verkeer, straatmeubilair', 'Verkeerslicht', STOPEC, "CCA,ASC,VRI"),
    ('F26', 'Wegen, verkeer, straatmeubilair', 'Overig wegen/verkeer/straatmeubilair', I5DMC, "CCA,ASC,STW"), # TODO : not in classificatie
    ('F27', 'Wegen, verkeer, straatmeubilair', 'Verkeersoverlast / Verkeerssituaties', I5DMC, "CCA,ASC,THO"),
    ('F28', 'Overlast in de openbare ruimte', 'Lozing / dumping / bodemverontreiniging', A3DMC, "CCA,ASC,OMG"),
    ('F29', 'Overlast in de openbare ruimte', 'Parkeeroverlast', A3DMC, "CCA,ASC,THO"),
    ('F30', 'Overlast in de openbare ruimte', 'Fietswrak', A3WMC, "CCA,ASC,STW,THO"),
    ('F31', 'Overlast in de openbare ruimte', 'Stank- / geluidsoverlast', A3WMC, "CCA,ASC,THO,VTH"),
    ('F32', 'Overlast in de openbare ruimte', 'Bouw- / sloopoverlast', A3WMC, "CCA,ASC,VTH"),
    ('F33', 'Overlast in de openbare ruimte', 'Auto- / scooter- / bromfiets(wrak)', A3WMC, "CCA,ASC,VTH"),
    ('F34', 'Overlast in de openbare ruimte', 'Graffiti / wildplak', I5DMC, "CCA,ASC,STW"),
    ('F35', 'Overlast in de openbare ruimte', 'Honden(poep)', A3WMC, "CCA,ASC,STW"),
    ('F36', 'Overlast in de openbare ruimte', 'Hinderlijk geplaatst object', I5DMC, "CCA,ASC,THO"),
    # vervallen ('F37','Overlast in de openbare ruimte','Overlast van dieren
    #  (bijv. ratten)', 'REST', "CCA,ASC"),
    # vervallen ('F38','Overlast in de openbare ruimte','Vuurwerkoverlast',
    # 'REST', "CCA,ASC"),
    ('F39', 'Overlast in de openbare ruimte', 'Deelfiets', A3WMC, "CCA,ASC,STW"),
    ('F40', 'Overlast in de openbare ruimte', 'Overig openbare ruimte', I5DMC, "CCA,ASC,STW,THOVTH"),
    ('F41', 'Openbaar groen en water', 'Boom', I5DMC, "CCA,ASC,STW"),
    ('F42', 'Openbaar groen en water', 'Maaien / snoeien', I5DMC, "CCA,ASC,STW"),
    ('F43', 'Openbaar groen en water', 'Onkruid', I5DMC, "CCA,ASC,STW"),
    ('F44', 'Openbaar groen en water', 'Drijfvuil', I5DMC, "CCA,ASC,STW"),
    ('F45', 'Openbaar groen en water', 'Oever / kade / steiger', I5DMC, "CCA,ASC,STW"),
    ('F46', 'Openbaar groen en water', 'Overig groen en water', I5DMC, "CCA,ASC,STW"),  # Not in meldingen classificatie
    # vervallen ('F47','Overlast van dieren','Hondenpoep', 'REST', "CCA,ASC"),
    ('F48', 'Overlast van dieren', 'Ratten', I5DMC, "CCA,ASC,GGD"),
    ('F49', 'Overlast van dieren', 'Ganzen', I5DMC, "CCA,ASC,GGD"),
    ('F50', 'Overlast van dieren', 'Duiven', I5DMC, "CCA,ASC,GGD"),
    ('F51', 'Overlast van dieren', 'Meeuwen', I5DMC, "CCA,ASC,GGD"),
    ('F52', 'Overlast van dieren', 'Wespen', I5DMC, "CCA,ASC,GGD"),
    ('F53', 'Overlast van dieren', 'Dode dieren', A3DMC, "CCA,ASC,GGD"),
    ('F54', 'Overlast van dieren', 'Overig dieren', I5DMC, "CCA,ASC,GGD"),
    ('F55a', 'Overlast van en door personen of groepen', 'Vuurwerkoverlast', A3DMC, "CCA,ASC,THO"),
    ('F55b', 'Overlast van en door personen of groepen', 'Overlast door afsteken vuurwerk', A3DMC, "CCA,ASC,THO"),
    ('F56', 'Overlast van en door personen of groepen', 'Overige overlast door personen', A3DMC, "CCA,ASC,THO"),
    ('F57', 'Overlast van en door personen of groepen', 'Personen op het water', A3DMC, "CCA,ASC,THO"),  # Not in meldingen  classificatie
    ('F58', 'Overlast van en door personen of groepen', "Overlast van taxi's, bussen en fietstaxi's", A3DMC, "CCA,ASC,THO"),
    ('F59', 'Overlast van en door personen of groepen', 'Jongerenoverlast', A3DMC, "CCA,ASC,THO"),
    ('F60', 'Overlast van en door personen of groepen', 'Daklozen / bedelen', A3DMC, "CCA,ASC,THO"),
    ('F61', 'Overlast van en door personen of groepen', 'Wildplassen / poepen / overgeven', A3DMC, "CCA,ASC,THO"),
    ('F62', 'Overlast van en door personen of groepen', 'Drank- en drugsoverlast', A3DMC, "CCA,ASC,THO"),
    ('F63', 'Overlast Bedrijven en Horeca', 'Geluidsoverlast muziek', I5DMC, "CCA,ASC,VTH"),
    ('F64', 'Overlast Bedrijven en Horeca', 'Geluidsoverlast installaties', I5DMC, "CCA,ASC,VTH"),
    ('F65', 'Overlast Bedrijven en Horeca', 'Overlast terrassen', I5DMC, "CCA,ASC,VTH"),
    ('F66a', 'Overlast Bedrijven en Horeca', 'Stank horeca/bedrijven', I5DMC, "CCA,ASC,VTH"),  # Niet in meldingen classificatie
    ('F66b', 'Overlast Bedrijven en Horeca', 'Stankoverlast', I5DMC, "CCA,ASC,VTH"),
    ('F67', 'Overlast Bedrijven en Horeca', 'Overlast door bezoekers (niet op terras)', I5DMC, "CCA,ASC,THO"), # Niet in meldingen classificatie
    ('F68', 'Overlast Bedrijven en Horeca', 'Overig horeca/bedrijven', I5DMC, "CCA,ASC,THO,VTH"),  # Niet in meldingen classificatie
    ('F69a', 'Overlast op het water', 'Overlast op het water - snel varen', WS1EC, "CCA,ASC,WAT"),
    ('F69b', 'Overlast op het water', 'Overlast op het water - Vaargedrag', WS1EC, "CCA,ASC,WAT"),
    ('F70', 'Overlast op het water', 'Overlast op het water - geluid', WS1EC, "CCA,ASC,WAT"),
    ('F71', 'Overlast op het water', 'Overlast op het water - Gezonken boot', WS2EC, "CCA,ASC,WAT"),
    ('F72a', 'Overlast op het water', 'Scheepvaart nautisch toezicht', WS1EC, "CCA,ASC,WAT"),
    ('F72b', 'Overlast op het water', 'Overlast vanaf het water', WS1EC, "CCA,ASC,WAT"),
    ('F72c', 'Overlast op het water', 'Overig boten', WS1EC, "CCA,ASC,WAT"), # Niet in meldingen classificatie
    ('F73', 'Overig', 'Overig', REST, "CCA,ASC")  # Niet in meldingen classificatie
)

SUB_CATEGORIES_DICT = {}
for entry in ALL_SUB_CATEGORIES:
    SUB_CATEGORIES_DICT[entry[2]] = entry

MAIN_CATEGORIES_DICT = {}
for entry in ALL_SUB_CATEGORIES:
    if SUB_CATEGORIES_DICT.get(entry[1]):
        SUB_CATEGORIES_DICT[entry[1]] += (entry,)
    else:
        SUB_CATEGORIES_DICT[entry[1]] = (entry,)

ALL_AFHANDELING_TEXT = {
    A3DMC: """
We laten u binnen 3 werkdagen weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",
    A3DEC: """
Wij handelen uw melding binnen 3 werkdagen af.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    A3WMC: """
We laten u binnen 3 weken weten wat we hebben gedaan. En anders hoort u wanneer wij uw melding kunnen oppakken.
We houden u op de hoogte via e-mail.""",
    A3WEC: """
Wij handelen uw melding binnen drie weken af.
En anders hoort u - via e-mail - wanneer wij uw melding kunnen oppakken.""",
    I5DMC: """
Uw melding wordt ingepland: wij laten u binnen 5 werkdagen weten hoe en wanneer uw melding wordt afgehandeld. Dat doen we via e-mail.""",
    STOPEC: """
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties handelen wij meestal binnen 5 werkdagen af.
Als we uw melding niet binnen 5 werkdagen kunnen afhandelen, hoort u - via e-mail – hoe wij uw melding oppakken.""",
    KLOKLICHTZC: """
Gevaarlijke situaties zullen wij zo snel mogelijk verhelpen, andere situaties kunnen wat langer duren. Wij kunnen u hier helaas niet altijd van op de hoogte houden.""",
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
    sub = SUB_CATEGORIES_DICT.get(sub_categorie)
    if sub:
        afhandeling_code = sub[3]
    else:
        afhandeling_code = REST
    return ALL_AFHANDELING_TEXT[afhandeling_code]


def get_departments(sub_categorie):
    sub = SUB_CATEGORIES_DICT.get(sub_categorie)
    if sub:
        departments = sub[4]
        #ldepartments = map( lambda x: ALL_DEPARTMENTS[x][0], departments.split(","))
        return departments
    else:
        return None
