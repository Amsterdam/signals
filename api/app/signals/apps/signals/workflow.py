"""
Model the workflow of responding to a Signal (melding) as state machine.
"""

# Internal statusses
LEEG = ''
GEMELD = 'm'
AFWACHTING = 'i'
BEHANDELING = 'b'
ON_HOLD = 'h'
AFGEHANDELD = 'o'
GEANNULEERD = 'a'

# Statusses to track progress in external systems
TE_VERZENDEN = 'ready to send'
VERZONDEN = 'send'
VERZENDEN_MISLUKT = 'send failed'
AFGEHANDELD_EXTERN = 'done external'

# Choices for the API/Serializer layer. Users that can change the state via the API are only allowed
# to use one of the following choices.
STATUS_CHOICES_API = (
    (GEMELD, 'Gemeld'),
    (AFWACHTING, 'In afwachting van behandeling'),
    (BEHANDELING, 'In behandeling'),
    (ON_HOLD, 'On hold'),
    (TE_VERZENDEN, 'Te verzenden naar extern systeem'),
    (AFGEHANDELD, 'Afgehandeld'),
    (GEANNULEERD, 'Geannuleerd'),
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

# Should chaning to "your self" be possible.
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
        AFWACHTING,
        BEHANDELING,
        ON_HOLD,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    BEHANDELING: [
        # AFWACHTING,  # This should be possible?
        BEHANDELING,
        ON_HOLD,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
    ON_HOLD: [
        GEMELD,  # Should this be possible?
        AFWACHTING,
        BEHANDELING,
        ON_HOLD,
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
