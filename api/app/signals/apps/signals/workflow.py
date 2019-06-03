"""
Model the workflow of responding to a Signal (melding) as state machine.
"""
# ! Made sure that the status that is created also exists in the ZTC on staging. Otherwise it will
# ! fail with setting the status.

# Internal statusses
LEEG = ''
GEMELD = 'm'
AFWACHTING = 'i'
BEHANDELING = 'b'
ON_HOLD = 'h'
AFGEHANDELD = 'o'
GEANNULEERD = 'a'
GESPLITST = 's'
HEROPEND = 'reopened'
VERZOEK_TOT_AFHANDELING = 'closure requested'
INGEPLAND = 'ingepland'

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
    (TE_VERZENDEN, 'Te verzenden naar extern systeem'),
    (AFGEHANDELD, 'Afgehandeld'),
    (GEANNULEERD, 'Geannuleerd'),
    (HEROPEND, 'Heropend'),
    (GESPLITST, 'Gesplitst'),
    (VERZOEK_TOT_AFHANDELING, 'Verzoek tot afhandeling'),
)

# Choices used by the application. These choices can be set from within the application, not via the
# API/Serializer layer.
STATUS_CHOICES_APP = (
    (VERZONDEN, 'Verzonden naar extern systeem'),
    (VERZENDEN_MISLUKT, 'Verzending naar extern systeem mislukt'),
    (AFGEHANDELD_EXTERN, 'Melding is afgehandeld in extern systeem'),
)

# All allowed choices, used for the model `Status`.
STATUS_CHOICES = STATUS_CHOICES_API + STATUS_CHOICES_APP

ALLOWED_STATUS_CHANGES = {
    LEEG: [
        GEMELD
    ],
    GEMELD: [
        GEMELD,  # SIG-1264
        GESPLITST,
        AFWACHTING,
        BEHANDELING,
        TE_VERZENDEN,
        AFGEHANDELD,  # SIG-1294
    ],
    AFWACHTING: [
        GEMELD,  # SIG-1264
        AFWACHTING,
        INGEPLAND,
        VERZOEK_TOT_AFHANDELING,
        AFGEHANDELD,
        TE_VERZENDEN,  # SIG-1293
        BEHANDELING,  # SIG-1295
    ],
    BEHANDELING: [
        GEMELD,  # SIG-1264
        INGEPLAND,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    INGEPLAND: [
        GEMELD,  # SIG-1264
        INGEPLAND,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        VERZOEK_TOT_AFHANDELING,  # SIG-1293
    ],
    ON_HOLD: [
        INGEPLAND,
    ],
    TE_VERZENDEN: [
        VERZONDEN,
        VERZENDEN_MISLUKT,
    ],
    VERZONDEN: [
        AFGEHANDELD_EXTERN,
    ],
    VERZENDEN_MISLUKT: [
        GEMELD,
        TE_VERZENDEN,
    ],
    AFGEHANDELD_EXTERN: [
        AFGEHANDELD,
        GEANNULEERD,
        BEHANDELING,  # SIG-1293
    ],
    AFGEHANDELD: [
        AFGEHANDELD,
        HEROPEND,
    ],
    GEANNULEERD: [
        GEANNULEERD,
        HEROPEND,
    ],
    HEROPEND: [
        HEROPEND,
        BEHANDELING,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    GESPLITST: [],
    VERZOEK_TOT_AFHANDELING: [
        GEMELD,  # SIG-1264
        VERZOEK_TOT_AFHANDELING,
        AFWACHTING,
        AFGEHANDELD,
        GEANNULEERD,
    ],
}
