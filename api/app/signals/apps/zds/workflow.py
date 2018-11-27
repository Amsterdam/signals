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
    LEEG: BASE_URL + '962dc7e7-d8be-4b37-a154-2486ec169973',
    GEMELD: BASE_URL + '1644c9c0-d559-4dee-b652-0e64aca73dd1',
    AFWACHTING: BASE_URL + '02d3ef74-7733-4bbe-8d6f-3884c5ea6f30',
    BEHANDELING: BASE_URL + 'cf36f5e7-3144-4e03-8c93-de5875ae36b4',
    ON_HOLD: BASE_URL + 'd019ff51-46f2-461c-90e3-b7255e7945ed',
    AFGEHANDELD: BASE_URL + 'a1dfddbd-af63-4860-817b-04b1d73ad5cf',
    GEANNULEERD: BASE_URL + 'cb77683b-b399-4514-8cf4-1a00f4b5abe8',
    TE_VERZENDEN: BASE_URL + 'f8cced3c-448a-4d78-b8f9-0b08085fa2a9',
    VERZONDEN: BASE_URL + 'ebbb1503-9c9a-4693-b4cf-2e0ad1db9255',
    VERZENDEN_MISLUKT: BASE_URL + '0a055aa3-add5-4138-bb58-afd852dc52c8',
    AFGEHANDELD_EXTERN: BASE_URL + 'c31a9df5-cb30-43f8-ab19-8052c27fe6c9',
}
