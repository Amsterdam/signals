"""
Test suite for Sigmax message generation.
"""
import logging
from unittest import mock

from django.test import TestCase

from signals.apps.sigmax.models import CityControlRoundtrip
from signals.apps.sigmax.stuf_protocol.exceptions import SigmaxException
from signals.apps.sigmax.stuf_protocol.outgoing import handle
from tests.apps.signals.factories import SignalFactory

logger = logging.getLogger(__name__)


class TestHandle(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create()

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

        with self.assertRaises(SigmaxException):
            handle(self.signal)
        patched_send_voegZaakdocumentToe_Lk01.assert_not_called()

    @mock.patch('signals.apps.sigmax.stuf_protocol.outgoing.send_creeerZaak_Lk01', autospec=True)
    @mock.patch(
        'signals.apps.sigmax.stuf_protocol.outgoing.send_voegZaakdocumentToe_Lk01', autospec=True)
    def test_success_message(self,
                             patched_send_voegZaakdocumentToe_Lk01,
                             patched_send_creeerZaak_Lk01):
        success_message = handle(self.signal)
        self.assertIn(
            '{}.01'.format(self.signal.sia_id),
            success_message
        )
