from unittest import mock

from django.test import TestCase
from freezegun import freeze_time

from signals.apps.email_integrations.flex_horeca import tasks
from tests.apps.signals.factories import SignalFactory


class TestTasks(TestCase):
    signal = None

    def setUp(self):
        self.signal = SignalFactory.create(
            category_assignment__category__parent__name='Overlast Bedrijven en Horeca',
            category_assignment__category__name='Geluidsoverlast muziek'
        )

    @freeze_time('2019-08-16T12:00:00+02:00')
    @mock.patch('signals.apps.email_integrations.flex_horeca.tasks.mail', autospec=True)
    def test_send_mail_flex_horeca(self, mocked_mail):
        tasks.send_mail_flex_horeca(pk=self.signal.id)
        mocked_mail.send_mail.assert_called_once_with(self.signal)

    @mock.patch('signals.apps.email_integrations.flex_horeca.tasks.mail', autospec=True)
    def test_send_mail_flex_horeca_signal_not_found(self, mocked_mail):
        tasks.send_mail_flex_horeca(pk=999)
        mocked_mail.send_mail.assert_not_called()
