"""
Send a signal (melding) to CityControl/Sigmax.
"""
import logging

from signals.apps.sigmax.app_settings import MAX_ROUND_TRIPS
from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.sigmax.stuf_protocol.exceptions import (
    CreeerZaakLk01Error,
    SentTooManyTimesError,
    VoegZaakDocumentToeLk01Error
)
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
        msg = f'Signal {signal.sia_id} was sent to SigmaxCityControl too often.'
        raise SentTooManyTimesError(msg)

    return '{0:02d}'.format(roundtrip_count + 1)  # start counting at one


def handle(signal: Signal) -> None:
    """
    Create a case (zaak) in Sigmax/CityControl, attach extra info in PDF
    """
    # We have to increment the sequence number in the CityControl external
    # identifier (e.g. the 01 in SIA-123.01). To do so we keep track of the
    # number of times an issue is sent to CityControl.
    seq_no = _generate_sequence_number(signal)  # may raise SentTooManyTimesError

    # First try to register a Signal (melding) with CityControl as a "zaak", if
    # this fails with network error or something like it catch the error and
    # reraise it as a CreeerZaakLk01Error.
    try:
        r1 = send_creeerZaak_Lk01(signal, seq_no)
    except Exception as e:
        raise CreeerZaakLk01Error from e

    # Check that CityControl accepts the Signal as a zaak, if not raise a
    # CreeerZaakLk01Error.
    if r1.status_code == 200:
        CityControlRoundtrip.objects.create(_signal=signal)
    else:
        msg = f'CityControl rejected {signal.sia_id}.{seq_no}'
        raise CreeerZaakLk01Error(msg)

    # If a Signal was successfully registered with CityControl try to follow it
    # up with a PDF containing the Signal information. Any errors in this
    # process are caught and converted to a VoegZaakDocumentToeLk01Error.
    try:
        send_voegZaakdocumentToe_Lk01(signal, seq_no)
    except Exception as e:
        raise VoegZaakDocumentToeLk01Error from e

    # Make sure to generate a success message for user-visible log.
    return 'Verzending van melding naar THOR is gelukt onder nummer {}.{}.'.format(
        signal.sia_id,
        seq_no,
    )
