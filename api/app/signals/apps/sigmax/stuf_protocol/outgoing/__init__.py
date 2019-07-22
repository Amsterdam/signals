"""
Handle sending a signal to sigmax.
Retry logic ao are handled by Celery.
"""
import logging

from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.sigmax.stuf_protocol.exceptions import SigmaxException
from signals.apps.sigmax.stuf_protocol.outgoing.creeerZaak_Lk01 import (
    MAX_ROUND_TRIPS,
    _generate_sequence_number,
    send_creeerZaak_Lk01
)
from signals.apps.sigmax.stuf_protocol.outgoing.voegZaakdocumentToe_Lk01 import (
    send_voegZaakdocumentToe_Lk01
)
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def handle(signal: Signal) -> None:
    """
    Create a case (zaak) in Sigmax/CityControl, attach extra info in PDF
    """
    # Refuse to send a `Signal` to CityControl if we have done so too many times
    # already.
    roundtrip_count = CityControlRoundtrip.objects.filter(_signal=signal).count()
    if not roundtrip_count < MAX_ROUND_TRIPS:
        raise SigmaxException(
            'Signal SIA-{} was sent to SigmaxCityControl too often.'.format(signal.sia_id))

    # Note: functions below may raise, exceptions are handled at Celery level.
    r1 = send_creeerZaak_Lk01(signal)
    send_voegZaakdocumentToe_Lk01(signal)

    # We have to increment the sequence number in the CityControl external
    # identifier (e.g. the 01 in SIA-123.01). To do so we keep track of the
    # number of times an issue is sent to CityControl.
    sequence_number = _generate_sequence_number(signal)  # before roundtrips are incremented
    if r1.status_code == 200:
        CityControlRoundtrip.objects.create(_signal=signal)

    # Make sure to generate a success message for user-visible log.
    return 'Verzending van melding naar THOR is gelukt onder nummer {}.{}.'.format(
        signal.sia_id,
        sequence_number,
    )
