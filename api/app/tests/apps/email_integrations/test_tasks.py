from unittest import mock

from django.test import TestCase

from signals.apps.email_integrations import tasks
from signals.apps.feedback.models import Feedback
from signals.apps.signals.models import Signal, Status
from tests.apps.signals.factories import SignalFactory


class TestTasks(TestCase):

    @mock.patch('signals.apps.email_integrations.tasks.core', autospec=True)
    def test_send_mail_reporter_created(self, mocked_core):
        signal = SignalFactory.create()

        tasks.send_mail_reporter_created(pk=signal.id)

        mocked_core.send_mail_reporter_created.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.core', autospec=True)
    def test_send_mail_reporter_created_signal_not_found(self, mocked_core):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_reporter_created(pk=999)

        mocked_core.send_mail_reporter_created.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.core', autospec=True)
    def test_send_mail_reporter_status_changed(self, mocked_core):
        signal = SignalFactory.create()

        tasks.send_mail_reporter_status_changed(signal_pk=signal.id, status_pk=signal.status.id)

        feedback = Feedback.objects.get(_signal=signal)
        mocked_core.send_mail_reporter_status_changed_afgehandeld.assert_called_once_with(
            signal, signal.status, feedback)

    @mock.patch('signals.apps.email_integrations.tasks.core', autospec=True)
    def test_send_mail_reporter_status_changed_status_not_found(self, mocked_core):
        SignalFactory.create(id=1)

        with self.assertRaises(Status.DoesNotExist):
            tasks.send_mail_reporter_status_changed(signal_pk=1, status_pk=999)

        mocked_core.send_mail_reporter_status_changed_afgehandeld.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.core', autospec=True)
    def test_send_mail_reporter_status_changed_split(self, mocked_core):
        signal = SignalFactory.create()

        tasks.send_mail_reporter_status_changed_split(
            signal_pk=signal.id, status_pk=signal.status.id)

        mocked_core.send_mail_reporter_status_changed_split.assert_called_once_with(
            signal, signal.status)

    @mock.patch('signals.apps.email_integrations.tasks.core', autospec=True)
    def test_send_mail_reporter_status_changed_split_signal_not_found(self, mocked_core):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_reporter_status_changed_split(signal_pk=999, status_pk=999)

        mocked_core.send_mail_reporter_status_changed_split.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.apptimize', autospec=True)
    def test_send_mail_apptimize(self, mocked_apptimize):
        signal = SignalFactory.create()

        tasks.send_mail_apptimize(pk=signal.id)

        mocked_apptimize.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.apptimize', autospec=True)
    def test_send_mail_apptimize_signal_not_found(self, mocked_apptimize):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_apptimize(pk=999)

        mocked_apptimize.send_mail.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.flex_horeca', autospec=True)
    def test_send_mail_flex_horeca(self, mocked_flex_horeca):
        signal = SignalFactory.create()

        tasks.send_mail_flex_horeca(pk=signal.id)

        mocked_flex_horeca.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.flex_horeca', autospec=True)
    def test_send_mail_flex_horeca_signal_not_found(self, mocked_flex_horeca):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_flex_horeca(pk=999)

        mocked_flex_horeca.send_mail.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.handhaving_or_oost', autospec=True)
    def test_send_mail_handhaving_or_oost(self, mocked_handhaving_or_oost):
        signal = SignalFactory.create()

        tasks.send_mail_handhaving_or_oost(pk=signal.id)

        mocked_handhaving_or_oost.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.handhaving_or_oost', autospec=True)
    def test_send_mail_handhaving_or_oost_signal_not_found(self, mocked_handhaving_or_oost):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_handhaving_or_oost(pk=999)

        mocked_handhaving_or_oost.send_mail.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.toezicht_or_nieuw_west', autospec=True)
    def test_send_mail_toezicht_or_nieuw_west(self, mocked_toezicht_or_nieuw_west):
        signal = SignalFactory.create()

        tasks.send_mail_toezicht_or_nieuw_west(pk=signal.id)

        mocked_toezicht_or_nieuw_west.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.toezicht_or_nieuw_west', autospec=True)
    def test_send_mail_toezicht_or_nieuw_west_signal_not_found(self, mocked_toezicht_or_nieuw_west):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_toezicht_or_nieuw_west(pk=999)

        mocked_toezicht_or_nieuw_west.send_mail.assert_not_called()

    @mock.patch('signals.apps.email_integrations.tasks.vth_nieuw_west', autospec=True)
    def test_send_mail_vth_nieuw_west(self, mocked_vth_nieuw_west):
        signal = SignalFactory.create()

        tasks.send_mail_vth_nieuw_west(pk=signal.id)

        mocked_vth_nieuw_west.send_mail.assert_called_once_with(signal)

    @mock.patch('signals.apps.email_integrations.tasks.vth_nieuw_west', autospec=True)
    def test_send_mail_vth_nieuw_west_signal_not_found(self, mocked_vth_nieuw_west):
        with self.assertRaises(Signal.DoesNotExist):
            tasks.send_mail_vth_nieuw_west(pk=999)

        mocked_vth_nieuw_west.send_mail.assert_not_called()
