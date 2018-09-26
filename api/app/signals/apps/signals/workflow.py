"""
Model the workflow of responding to a Signal (melding) as state machine.
"""

# SIA internal statusses
LEEG = ''
GEMELD = 'm'
AFWACHTING = 'i'
BEHANDELING = 'b'
AFGEHANDELD = 'o'
ON_HOLD = 'h'
GEANNULEERD = 'a'
STATUS_OPTIONS_API = (
    (GEMELD, 'Gemeld'),
    (AFWACHTING, 'In afwachting van behandeling'),
    (BEHANDELING, 'In behandeling'),
    (AFGEHANDELD, 'Afgehandeld'),
    (ON_HOLD, 'On hold'),
    (GEANNULEERD, 'Geannuleerd')
)

# SIA statusses to track progress in external systems
TE_VERZENDEN = 'T'
VERZONDEN = 'V'
VERZENDEN_MISLUKT = 'M'
AFGEHANDELD_EXTERN = 'A'

STATUS_OPTIONS_EXTERNAL_SYSTEMS = (
    (TE_VERZENDEN, 'Te verzenden naar extern systeem.'),
    (VERZONDEN, 'Verzonden naar extern systeem.'),
    (VERZENDEN_MISLUKT, 'Verzending naar extern systeem mislukt'),
    (AFGEHANDELD_EXTERN, 'Melding is afgehandeld in extern systeem.'),
)

STATUS_OPTIONS = STATUS_OPTIONS_API + STATUS_OPTIONS_EXTERNAL_SYSTEMS

STATUS_OVERGANGEN = {
    LEEG: [
        GEMELD  # Een nieuw melding mag alleen aangemaakt worden met gemeld
    ],
    GEMELD: [
        AFGEHANDELD,
        AFWACHTING,
        BEHANDELING,
        GEANNULEERD,
        GEMELD,
        ON_HOLD,
        TE_VERZENDEN,
    ],
    AFWACHTING: [
        AFGEHANDELD,
        AFWACHTING,
        BEHANDELING,
        GEANNULEERD,
        ON_HOLD,
        TE_VERZENDEN,
    ],
    BEHANDELING: [
        AFGEHANDELD,
        BEHANDELING,
        GEANNULEERD,
        ON_HOLD,
        TE_VERZENDEN,
    ],
    ON_HOLD: [
        AFGEHANDELD,
        AFWACHTING,
        BEHANDELING,
        GEANNULEERD,
        GEMELD,
        TE_VERZENDEN,
    ],
    AFGEHANDELD: [],
    GEANNULEERD: [],
    TE_VERZENDEN: [
        VERZONDEN,
        VERZENDEN_MISLUKT,
    ],
    VERZONDEN: [
        AFGEHANDELD_EXTERN,
    ],
    AFGEHANDELD_EXTERN: [
        AFGEHANDELD,
        GEANNULEERD,
    ],
}
