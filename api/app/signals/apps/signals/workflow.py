# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
"""
Model the workflow of responding to a Signal (melding) as state machine.
"""
# Note on historical states: to leave the historical data intact, old states are
# retained below (but made unreachable if at all possible).

# Internal statusses
LEEG = ''
GEMELD = 'm'
AFWACHTING = 'i'
BEHANDELING = 'b'
ON_HOLD = 'h'
AFGEHANDELD = 'o'
GEANNULEERD = 'a'
GESPLITST = 's'  # Historical state - new `signal.Signal` instances will not get this state ever.
HEROPEND = 'reopened'
VERZOEK_TOT_AFHANDELING = 'closure requested'
INGEPLAND = 'ingepland'
VERZOEK_TOT_HEROPENEN = 'reopen requested'
REACTIE_GEVRAAGD = 'reaction requested'
REACTIE_ONTVANGEN = 'reaction received'
DOORGEZET_NAAR_EXTERN = 'forward to external'

# Statusses to track progress in external systems
TE_VERZENDEN = 'ready to send'
VERZONDEN = 'sent'
VERZENDEN_MISLUKT = 'send failed'
AFGEHANDELD_EXTERN = 'done external'

# Choices for the API/Serializer layer. Users that can change the state via the API are only allowed
# to use one of the following choices.
STATUS_CHOICES_API = (
    (GEMELD, 'Gemeld'),
    (AFWACHTING, 'In afwachting van behandeling'),
    (BEHANDELING, 'In behandeling'),
    (ON_HOLD, 'On hold'),
    (INGEPLAND, 'Ingepland'),
    (TE_VERZENDEN, 'Extern: te verzenden'),
    (AFGEHANDELD, 'Afgehandeld'),
    (GEANNULEERD, 'Geannuleerd'),
    (HEROPEND, 'Heropend'),
    (GESPLITST, 'Gesplitst'),
    (VERZOEK_TOT_AFHANDELING, 'Extern: verzoek tot afhandeling'),
    (REACTIE_GEVRAAGD, 'Reactie gevraagd'),
    (REACTIE_ONTVANGEN, 'Reactie ontvangen'),
    (DOORGEZET_NAAR_EXTERN, 'Doorzetten naar extern'),
)

# Choices used by the application. These choices can be set from within the application, not via the
# API/Serializer layer.
STATUS_CHOICES_APP = (
    (VERZONDEN, 'Extern: verzonden'),
    (VERZENDEN_MISLUKT, 'Extern: mislukt'),
    (AFGEHANDELD_EXTERN, 'Extern: afgehandeld'),
    (VERZOEK_TOT_HEROPENEN, 'Verzoek tot heropenen'),
)

# All allowed choices, used for the model `Status`.
STATUS_CHOICES = STATUS_CHOICES_API + STATUS_CHOICES_APP

ALLOWED_STATUS_CHANGES = {
    LEEG: [
        GEMELD
    ],
    GEMELD: [
        GEMELD,  # SIG-1264
        AFWACHTING,
        BEHANDELING,
        TE_VERZENDEN,
        AFGEHANDELD,  # SIG-1294
        GEANNULEERD,  # Op verzoek via mail van Arvid Smits
        INGEPLAND,  # SIG-1327
        REACTIE_GEVRAAGD,  # SIG-3651
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    AFWACHTING: [
        GEMELD,  # SIG-1264
        AFWACHTING,
        INGEPLAND,
        VERZOEK_TOT_AFHANDELING,
        AFGEHANDELD,
        TE_VERZENDEN,  # SIG-1293
        BEHANDELING,  # SIG-1295
        GEANNULEERD,  # SIG-2987
        REACTIE_GEVRAAGD,  # SIG-3651
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    BEHANDELING: [
        GEMELD,  # SIG-1264
        INGEPLAND,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
        VERZOEK_TOT_AFHANDELING,  # SIG-1374
        REACTIE_GEVRAAGD,  # SIG-3651
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    INGEPLAND: [
        GEMELD,  # SIG-1264
        INGEPLAND,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        VERZOEK_TOT_AFHANDELING,  # SIG-1293
        REACTIE_GEVRAAGD,  # SIG-3651
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    ON_HOLD: [
        INGEPLAND,
        GEANNULEERD,  # SIG-2987
    ],
    TE_VERZENDEN: [
        VERZONDEN,
        VERZENDEN_MISLUKT,
        GEANNULEERD,  # SIG-2987
    ],
    VERZONDEN: [
        AFGEHANDELD_EXTERN,
        GEANNULEERD,  # SIG-2987
    ],
    VERZENDEN_MISLUKT: [
        GEMELD,
        TE_VERZENDEN,
        GEANNULEERD,  # SIG-2987
    ],
    AFGEHANDELD_EXTERN: [
        AFGEHANDELD,
        GEANNULEERD,
        BEHANDELING,  # SIG-1293
    ],
    AFGEHANDELD: [
        HEROPEND,
        VERZOEK_TOT_HEROPENEN,
    ],
    GEANNULEERD: [
        GEANNULEERD,
        HEROPEND,
        BEHANDELING,  # SIG-2109
    ],
    HEROPEND: [
        HEROPEND,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
        GEMELD,  # SIG-1374
        REACTIE_GEVRAAGD,  # SIG-3948
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    GESPLITST: [],
    VERZOEK_TOT_AFHANDELING: [
        GEMELD,  # SIG-1264
        VERZOEK_TOT_AFHANDELING,
        AFWACHTING,
        AFGEHANDELD,
        GEANNULEERD,
        BEHANDELING,  # SIG-1374
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    VERZOEK_TOT_HEROPENEN: [
        AFGEHANDELD,
        HEROPEND,
        GEANNULEERD,
    ],
    REACTIE_GEVRAAGD: [  # SIG-3651
        GEMELD,
        AFWACHTING,
        BEHANDELING,
        INGEPLAND,
        AFGEHANDELD,
        GEANNULEERD,
        REACTIE_GEVRAAGD,
        REACTIE_ONTVANGEN,
        TE_VERZENDEN,
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    REACTIE_ONTVANGEN: [  # SIG-3651
        GEMELD,
        AFWACHTING,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        INGEPLAND,
        REACTIE_GEVRAAGD,
        TE_VERZENDEN,
        DOORGEZET_NAAR_EXTERN,  # PS-261
    ],
    DOORGEZET_NAAR_EXTERN: [
        VERZOEK_TOT_AFHANDELING,
        GEMELD,
        AFWACHTING,
        BEHANDELING,
        DOORGEZET_NAAR_EXTERN,
        INGEPLAND,
        AFGEHANDELD,
        GEANNULEERD,
        REACTIE_GEVRAAGD,
        REACTIE_ONTVANGEN,
        TE_VERZENDEN,
    ]
}
