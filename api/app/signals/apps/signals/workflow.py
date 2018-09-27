"""
Model the workflow of responding to a Signal (melding) as state machine.
"""

# SIA internal statusses
LEEG = ''
GEMELD = 'm'
AFWACHTING = 'i'
BEHANDELING = 'b'
ON_HOLD = 'h'
AFGEHANDELD = 'o'
GEANNULEERD = 'a'
STATUS_OPTIONS_API = (
    (GEMELD, 'Gemeld'),
    (AFWACHTING, 'In afwachting van behandeling'),
    (BEHANDELING, 'In behandeling'),
    (ON_HOLD, 'On hold'),
    (AFGEHANDELD, 'Afgehandeld'),
    (GEANNULEERD, 'Geannuleerd')
)

# SIA statusses to track progress in external systems
TE_VERZENDEN = 'ready to send'
VERZONDEN = 'send'
VERZENDEN_MISLUKT = 'send failed'
AFGEHANDELD_EXTERN = 'done external'
STATUS_OPTIONS_EXTERNAL_SYSTEMS = (
    (TE_VERZENDEN, 'Te verzenden naar extern systeem'),
    (VERZONDEN, 'Verzonden naar extern systeem'),
    (VERZENDEN_MISLUKT, 'Verzending naar extern systeem mislukt'),
    (AFGEHANDELD_EXTERN, 'Melding is afgehandeld in extern systeem'),
)

STATUS_CHOICES = STATUS_OPTIONS_API + STATUS_OPTIONS_EXTERNAL_SYSTEMS

ALLOWED_STATUS_CHANGES = {
    LEEG: [
        GEMELD
    ],
    GEMELD: [
        GEMELD,
        AFWACHTING,
        BEHANDELING,
        ON_HOLD,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    AFWACHTING: [
        # GEMELD,      ???
        AFWACHTING,
        BEHANDELING,
        ON_HOLD,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    BEHANDELING: [
        # GEMELD,      ???
        # AFWACHTING,  ???
        BEHANDELING,
        ON_HOLD,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    ON_HOLD: [
        GEMELD,
        AFWACHTING,
        BEHANDELING,
        # ON_HOLD,  ????
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
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
    ],
    AFGEHANDELD: [],
    GEANNULEERD: [],
}
