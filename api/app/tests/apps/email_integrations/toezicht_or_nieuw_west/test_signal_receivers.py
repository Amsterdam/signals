from unittest import mock

from django.test import TestCase

from signals.apps.signals.managers import create_child, create_initial
from signals.apps.signals.models import STADSDEEL_NIEUWWEST
from tests.apps.signals.factories import SignalFactory


class TestSignalReceivers(TestCase):
    signal = None

    def setUp(self):
        self.signal = SignalFactory.create(
            category_assignment__category__parent__name='Overlast in de openbare ruimte',
            category_assignment__category__name='Parkeeroverlast',
            location__stadsdeel=STADSDEEL_NIEUWWEST
        )

    @mock.patch('signals.apps.email_integrations.toezicht_or_nieuw_west.signal_receivers.tasks',
                autospec=True)
    def test_create_initial_handler(self, mocked_tasks):
        create_initial.send_robust(sender=self.__class__, signal_obj=self.signal)
        mocked_tasks.send_mail_toezicht_or_nieuw_west.delay.assert_called_once_with(
            pk=self.signal.id
        )

    @mock.patch('signals.apps.email_integrations.toezicht_or_nieuw_west.signal_receivers.tasks',
                autospec=True)
    def test_create_child_handler(self, mocked_tasks):
        create_child.send_robust(sender=self.__class__, signal_obj=self.signal)
        mocked_tasks.send_mail_toezicht_or_nieuw_west.delay.assert_called_once_with(
            pk=self.signal.id
        )
