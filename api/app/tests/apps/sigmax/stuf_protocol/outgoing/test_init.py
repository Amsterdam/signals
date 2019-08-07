"""
Test suite for Sigmax message generation.
"""
import logging
from unittest import mock

from django.test import TestCase

from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.sigmax.stuf_protocol.exceptions import (
    CreeerZaakLk01Error,
    SentTooManyTimesError,
    VoegZaakDocumentToeLk01Error
)
from signals.apps.sigmax.stuf_protocol.outgoing import handle
from signals.apps.signals import workflow
from signals.apps.signals.models import Status
from tests.apps.signals.factories import SignalFactory

logger = logging.getLogger(__name__)


class TestHandle(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(status__state=workflow.TE_VERZENDEN)

    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.MAX_ROUND_TRIPS', 2)
    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.send_creeerZaak_Lk01', autospec=True)
    @mock.patch(
        'signals.apps.sigmax.stuf_protocol.outgoing.send_voegZaakdocumentToe_Lk01', autospec=True)
    def test_too_many(self,
                      patched_send_voegZaakdocumentToe_Lk01,
                      patched_send_creeerZaak_Lk01,):
        CityControlRoundtrip.objects.create(_signal=self.signal)
        CityControlRoundtrip.objects.create(_signal=self.signal)
        CityControlRoundtrip.objects.create(_signal=self.signal)

        with self.assertRaises(SentTooManyTimesError):
            handle(self.signal)
        patched_send_voegZaakdocumentToe_Lk01.assert_not_called()

    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.send_creeerZaak_Lk01', autospec=True)
    @mock.patch(
        'signals.apps.sigmax.stuf_protocol.outgoing.send_voegZaakdocumentToe_Lk01', autospec=True)
    def test_success_message(self,
                             patched_send_voegZaakdocumentToe_Lk01,
                             patched_send_creeerZaak_Lk01):
        success_response = mock.Mock()
        success_response.status_code = 200
        patched_send_creeerZaak_Lk01.return_value = success_response

        handle(self.signal)
        self.signal.refresh_from_db()

        last_status = Status.objects.filter(_signal=self.signal).order_by('id').last()
        self.assertIn(
             f'Verzending van melding naar THOR is gelukt onder nummer {self.signal.sia_id}.01.',  # noqa
             last_status.text,
        )

    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.send_signal_and_pdf', autospec=True)
    def test_CreeerZaakLk01Error(self, patched_send_signal_and_pdf):
        patched_send_signal_and_pdf.side_effect = CreeerZaakLk01Error('this is a test')

        with self.assertRaises(CreeerZaakLk01Error):
            handle(self.signal)

        self.signal.refresh_from_db()
        self.assertEqual(self.signal.status.state, workflow.VERZENDEN_MISLUKT)
        self.assertEqual(self.signal.status.text, 'Verzending van melding naar THOR is mislukt.')

    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.send_signal_and_pdf', autospec=True)
    def test_VoegZaakDocumentToeLk01Error(self, patched_send_signal_and_pdf):
        patched_send_signal_and_pdf.side_effect = VoegZaakDocumentToeLk01Error('this is a test')

        handle(self.signal)

        self.signal.refresh_from_db()

        self.assertEqual(self.signal.status.state, workflow.VERZONDEN)
        self.assertIn('Let op: waarschijnlijk is de PDF niet verzonden naar CityControl.',
                      self.signal.status.text)
