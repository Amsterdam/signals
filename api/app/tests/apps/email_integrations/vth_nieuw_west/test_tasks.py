from unittest import mock

from django.test import TestCase
from freezegun import freeze_time

from signals.apps.email_integrations.vth_nieuw_west import tasks
from signals.apps.signals.models import STADSDEEL_NIEUWWEST
from tests.apps.signals.factories import SignalFactory


class TestTasks(TestCase):
    signal = None

    def setUp(self):
        self.signal = SignalFactory.create(
            category_assignment__category__parent__name='Overlast Bedrijven en Horeca',
            category_assignment__category__name='Overlast terrassen',
            location__stadsdeel=STADSDEEL_NIEUWWEST
        )

    @freeze_time('2019-08-13T00:00:00+02:00')
    @mock.patch('signals.apps.email_integrations.vth_nieuw_west.tasks.mail', autospec=True)
    def test_send_mail_vth_nieuw_west(self, mocked_mail):
        tasks.send_mail_vth_nieuw_west(pk=self.signal.id)
        mocked_mail.send_mail.assert_called_once_with(self.signal)

    @mock.patch('signals.apps.email_integrations.vth_nieuw_west.tasks.mail', autospec=True)
    def test_send_mail_vth_nieuw_west_signal_not_found(self, mocked_mail):
        tasks.send_mail_vth_nieuw_west(pk=999)
        mocked_mail.send_mail.assert_not_called()
