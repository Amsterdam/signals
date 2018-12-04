from django.conf import settings

from signals.apps.signals.workflow import (
    AFGEHANDELD,
    AFGEHANDELD_EXTERN,
    AFWACHTING,
    BEHANDELING,
    GEANNULEERD,
    GEMELD,
    LEEG,
    ON_HOLD,
    TE_VERZENDEN,
    VERZENDEN_MISLUKT,
    VERZONDEN
)

# This is a wrapper for the ZTC statusses.
# This needs to be filled with links to the ZTC status.
BASE_URL = '{}/statustypen/'.format(settings.ZTC_ZAAKTYPE_URL)

ZTC_STATUSSES = {
    LEEG: BASE_URL + 'b59f487b-74c3-45f3-9130-24b2040bb1f6',
    GEMELD: BASE_URL + '70ae2e9d-73a2-4f3d-849e-e0a29ef3064e',
    AFWACHTING: BASE_URL + '04f5187d-4db8-456a-8390-42b930ee3fed',
    BEHANDELING: BASE_URL + '0d60e7c8-ca2c-48d5-aaa4-d6a6e75a9f08',
    ON_HOLD: BASE_URL + '462de26a-a049-4c5e-9c14-75b69a678f58',
    AFGEHANDELD: BASE_URL + '0fd576e2-74a9-4324-89cc-3dd5525dfd53',
    GEANNULEERD: BASE_URL + 'beb8d603-05b2-4200-aaf5-16ed69aca25a',
    TE_VERZENDEN: BASE_URL + 'f8cced3c-448a-4d78-b8f9-0b08085fa2a9',
    VERZONDEN: BASE_URL + 'ebbb1503-9c9a-4693-b4cf-2e0ad1db9255',
    VERZENDEN_MISLUKT: BASE_URL + '0a055aa3-add5-4138-bb58-afd852dc52c8',
    AFGEHANDELD_EXTERN: BASE_URL + 'c31a9df5-cb30-43f8-ab19-8052c27fe6c9',
}
