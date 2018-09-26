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
STATUS_OPTIONS = (
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

STATUS_OPTIONS_EXTERNAL = (
    (TE_VERZENDEN, 'Te verzenden naar extern systeem.'),
    (VERZONDEN, 'Verzonden naar extern systeem.'),
    (VERZENDEN_MISLUKT, 'Verzending naar extern systeem mislukt'),
    (AFGEHANDELD_EXTERN, 'Melding is afgehandeld in extern systeem.'),
)

# The state machine is used to check POSTs in the status serializer, hence below we
# leave out certain transitions that are possible --- but, not through the API.
# E.g. TE_VERZENDEN -> VERZENDEN_MISLUKT is only possible at the system level.

STATUS_OVERGANGEN = {
    LEEG: [GEMELD],  # Een nieuw melding mag alleen aangemaakt worden met gemeld
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
        VERZONDEN,  # Do not allow transition to VERZENDEN_MISLUKT (see comment above)
    ],
    VERZONDEN: [
        AFGEHANDELD_EXTERN,
    ],
    AFGEHANDELD_EXTERN: [
        AFGEHANDELD,
        GEANNULEERD,
    ],
}
