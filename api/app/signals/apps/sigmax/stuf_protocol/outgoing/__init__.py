"""
Send a signal (melding) to CityControl/Sigmax.
"""
import logging

from signals.apps.sigmax.app_settings import MAX_ROUND_TRIPS
from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.sigmax.stuf_protocol.exceptions import SigmaxException
from signals.apps.sigmax.stuf_protocol.outgoing.creeerZaak_Lk01 import send_creeerZaak_Lk01
from signals.apps.sigmax.stuf_protocol.outgoing.voegZaakdocumentToe_Lk01 import (
    send_voegZaakdocumentToe_Lk01
)
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def _generate_sequence_number(signal):
    """Generate a sequence number for external identifier in CityControl."""
    roundtrip_count = CityControlRoundtrip.objects.filter(_signal=signal).count()

    if not roundtrip_count < MAX_ROUND_TRIPS:  # check not sent too often
        msg = f'Signal SIA-{signal.sia_id} was sent to SigmaxCityControl too often.'
        raise SigmaxException(msg)

    return '{0:02d}'.format(roundtrip_count + 1)  # start counting at one


def handle(signal: Signal) -> None:
    """
    Create a case (zaak) in Sigmax/CityControl, attach extra info in PDF
    """
    # We have to increment the sequence number in the CityControl external
    # identifier (e.g. the 01 in SIA-123.01). To do so we keep track of the
    # number of times an issue is sent to CityControl.
    seq_no = _generate_sequence_number(signal)  # before roundtrips are incremented

    # Note: functions below may raise, exceptions are handled at Celery level.
    r1 = send_creeerZaak_Lk01(signal, seq_no)
    send_voegZaakdocumentToe_Lk01(signal, seq_no)

    if r1.status_code == 200:
        CityControlRoundtrip.objects.create(_signal=signal)

    # Make sure to generate a success message for user-visible log.
    return 'Verzending van melding naar THOR is gelukt onder nummer {}.{}.'.format(
        signal.sia_id,
        seq_no,
    )
