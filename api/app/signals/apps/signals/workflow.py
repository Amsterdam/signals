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

HEROPEND = 'reopened'

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
    (TE_VERZENDEN, 'Te verzenden naar extern systeem'),
    (AFGEHANDELD, 'Afgehandeld'),
    (GEANNULEERD, 'Geannuleerd'),
    (HEROPEND, 'Heropend'),
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

# TODO, Should changing to "your self" be possible. Currently it's used to update the text field
# with notes to other users.
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
    AFGEHANDELD: [
        HEROPEND,
    ],
    GEANNULEERD: [
        HEROPEND,
    ],
    # TODO: Check assumption that HEROPEND has equivalent role to GEMELD. Note
    # that this leads to many new transitions in the workflow state machine.
    HEROPEND: [
        AFWACHTING,
        BEHANDELING,
        ON_HOLD,
        AFGEHANDELD,
        GEANNULEERD,
        TE_VERZENDEN,
    ],
}

# This is a wrapper for the ZTC statusses.
# This needs to be filled with links to the ZTC status.
ZTC_STATUSSES = {
    LEEG: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/962dc7e7-d8be-4b37-a154-2486ec169973',
    GEMELD: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/1644c9c0-d559-4dee-b652-0e64aca73dd1',
    AFWACHTING: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/02d3ef74-7733-4bbe-8d6f-3884c5ea6f30',
    BEHANDELING: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/cf36f5e7-3144-4e03-8c93-de5875ae36b4',
    ON_HOLD: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/d019ff51-46f2-461c-90e3-b7255e7945ed',
    AFGEHANDELD: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/a1dfddbd-af63-4860-817b-04b1d73ad5cf',
    GEANNULEERD: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/cb77683b-b399-4514-8cf4-1a00f4b5abe8',
    TE_VERZENDEN: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/f8cced3c-448a-4d78-b8f9-0b08085fa2a9',
    VERZONDEN: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/ebbb1503-9c9a-4693-b4cf-2e0ad1db9255',
    VERZENDEN_MISLUKT: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/0a055aa3-add5-4138-bb58-afd852dc52c8',
    AFGEHANDELD_EXTERN: 'http://localhost:8004/api/v1/catalogussen/7d7d3ac9-a08b-427a-b4e1-1dc406790285/zaaktypen/80d93a21-bd7d-4cc6-8c54-97e1cdd0ddfd/statustypen/c31a9df5-cb30-43f8-ab19-8052c27fe6c9',
}
