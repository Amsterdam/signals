"""
Model the workflow of responding to a Signal (melding) as state machine.
"""

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

STATUS_OVERGANGEN = {
    LEEG: [GEMELD],  # Een nieuw melding mag alleen aangemaakt worden met gemeld
    GEMELD: [AFWACHTING, GEANNULEERD, ON_HOLD, GEMELD, BEHANDELING, AFGEHANDELD],
    AFWACHTING: [BEHANDELING, ON_HOLD, AFWACHTING, GEANNULEERD, AFGEHANDELD],
    BEHANDELING: [AFGEHANDELD, ON_HOLD, GEANNULEERD, BEHANDELING],
    ON_HOLD: [AFWACHTING, BEHANDELING, GEANNULEERD, GEMELD, AFGEHANDELD],
    AFGEHANDELD: [],
    GEANNULEERD: [],
}
