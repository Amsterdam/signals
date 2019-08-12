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
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def _generate_sequence_number(signal):
    """Generate a sequence number for external identifier in CityControl."""
    roundtrip_count = CityControlRoundtrip.objects.filter(_signal=signal).count()

    if not roundtrip_count < MAX_ROUND_TRIPS:  # check not sent too often
        msg = f'Signal {signal.sia_id} was sent to SigmaxCityControl too often.'
        raise SentTooManyTimesError(msg)

    return '{0:02d}'.format(roundtrip_count + 1)  # start counting at one


def send_signal_and_pdf(signal, seq_no):
    """
    Create a case (zaak) in Sigmax/CityControl, attach extra info in PDF
    """
    # First try to register a Signal (melding) with CityControl as a "zaak", if
    # this fails with network error or something like it catch the error and
    # reraise it as a CreeerZaakLk01Error.
    try:
        r1 = send_creeerZaak_Lk01(signal, seq_no)
    except Exception as e:
        raise CreeerZaakLk01Error from e

    # Check that CityControl accepts the Signal as a zaak, if not raise a
    # CreeerZaakLk01Error. On success, increment sequence number (which is
    # based on the number of CityControlRoundtrip entries).
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


def handle(signal):
    """
    Handle sending Signal (melding) and PDF to CityControl.
    """
    # Generate a sequence number for use in the CityControl external identifier
    # (e.g. the 01 in SIA-123.01).
    try:
        seq_no = _generate_sequence_number(signal)
    except SentTooManyTimesError:
        Signal.actions.update_status({
            'state': workflow.VERZENDEN_MISLUKT,
            'text': 'Verzending van melding naar THOR is mislukt.'
                    'Melding is te vaak verzonden.',
        }, signal=signal)
        raise  # Fail task in Celery.

    # Send the Signal to Sigmax, and follow up with PDF. Handle various success
    # and failure scenarios. Note: does not handle scenarios where the SOAP
    # request was successful but the response never reached SIA because of
    # network problems (this problem was observed, but rare).
    succ_msg = f'Verzending van melding naar THOR is gelukt onder nummer {signal.sia_id}.{seq_no}.'
    try:
        send_signal_and_pdf(signal, seq_no)
    except CreeerZaakLk01Error:
        Signal.actions.update_status({
            'state': workflow.VERZENDEN_MISLUKT,
            'text': 'Verzending van melding naar THOR is mislukt.',
        }, signal=signal)
        raise  # Fail task in Celery.
    except VoegZaakDocumentToeLk01Error:
        pdf_warning = 'Let op: waarschijnlijk is de PDF niet verzonden naar CityControl.'
        Signal.actions.update_status({
            'state': workflow.VERZONDEN,
            'text': f'{succ_msg} {pdf_warning}'
        }, signal=signal)
    else:
        Signal.actions.update_status({
            'state': workflow.VERZONDEN,
            'text': succ_msg,
        }, signal=signal)
