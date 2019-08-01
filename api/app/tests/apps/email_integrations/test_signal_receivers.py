from unittest import mock

from django.test import TestCase

from signals.apps.signals.managers import (
    create_child,
    create_initial,
    update_category_assignment,
    update_location,
    update_reporter,
    update_status
)
from tests.apps.signals.factories import (
    CategoryAssignmentFactory,
    LocationFactory,
    ReporterFactory,
    SignalFactory,
    StatusFactory
)


class TestSignalReceivers(TestCase):

    @mock.patch('signals.apps.zds.signal_receivers.tasks', autospec=True)
    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_create_initial_handler(self, mocked_tasks, zds_tasks):
        signal = SignalFactory.create()
        create_initial.send_robust(sender=self.__class__, signal_obj=signal)

        mocked_tasks.send_mail_reporter_created.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_flex_horeca.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_toezicht_or_nieuw_west.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_vth_nieuw_west.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_location_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_location = signal.location
        new_location = LocationFactory.create(_signal=signal)
        signal.location = new_location
        signal.save()

        signal = SignalFactory.create()

        update_location.send_robust(sender=self.__class__,
                                    signal_obj=signal,
                                    location=new_location,
                                    prev_location=prev_location)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_status_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_status = signal.status
        new_status = StatusFactory.create(_signal=signal)
        signal.status = new_status
        signal.save()

        update_status.send_robust(sender=self.__class__,
                                  signal_obj=signal,
                                  status=new_status,
                                  prev_status=prev_status)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_reporter_status_changed.delay.assert_called_once_with(
            signal_pk=signal.id, status_pk=new_status.id)
        mocked_tasks.send_mail_reporter_status_changed_heropend.delay.assert_called_once_with(
            signal_pk=signal.pk, status_pk=new_status.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_category_assignment_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_category_assignment = signal.category_assignment
        new_category_assignment = CategoryAssignmentFactory.create(_signal=signal)
        signal.category_assignment = new_category_assignment
        signal.save()

        update_category_assignment.send_robust(sender=self.__class__,
                                               signal_obj=signal,
                                               category_assignment=new_category_assignment,
                                               prev_category_assignment=prev_category_assignment)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_flex_horeca.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_reporter_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_reporter = signal.reporter
        new_reporter = ReporterFactory.create(_signal=signal)
        signal.reporter = new_reporter
        signal.save()

        update_reporter.send_robust(sender=self.__class__,
                                    signal_obj=signal,
                                    reporter=new_reporter,
                                    prev_reporter=prev_reporter)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_create_child_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        create_child.send_robust(sender=self.__class__, signal_obj=signal)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_flex_horeca.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_toezicht_or_nieuw_west.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_vth_nieuw_west.delay.assert_called_once_with(pk=signal.id)
