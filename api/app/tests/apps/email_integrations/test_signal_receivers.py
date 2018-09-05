from unittest import mock

from django.test import TestCase

from signals.apps.signals.models import (
    create_initial,
    update_category,
    update_location,
    update_reporter,
    update_status
)
from tests.apps.signals.factories import (
    CategoryFactory,
    LocationFactory,
    ReporterFactory,
    SignalFactory,
    StatusFactory
)


class TestSignalReceivers(TestCase):

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_create_initial_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        create_initial.send(sender=self.__class__, signal_obj=signal)

        mocked_tasks.send_mail_reporter.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_flex_horeca.delay.assert_called_once_with(pk=signal.id)
        mocked_tasks.send_mail_handhaving_or.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_location_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_location = signal.location
        new_location = LocationFactory.create(_signal=signal)
        signal.location = new_location
        signal.save()

        signal = SignalFactory.create()

        update_location.send(sender=self.__class__,
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

        update_status.send(sender=self.__class__,
                           signal_obj=signal,
                           status=new_status,
                           prev_status=prev_status)

        mocked_tasks.send_mail_status_change.delay.assert_called_once_with(
            status_pk=new_status.id,
            prev_status_pk=prev_status.id)
        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_category_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_category = signal.category
        new_category = CategoryFactory.create(_signal=signal)
        signal.category = new_category
        signal.save()

        update_category.send(sender=self.__class__,
                             signal_obj=signal,
                             category=new_category,
                             prev_category=prev_category)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)

    @mock.patch('signals.apps.email_integrations.signal_receivers.tasks', autospec=True)
    def test_update_reporter_handler(self, mocked_tasks):
        signal = SignalFactory.create()
        prev_reporter = signal.reporter
        new_reporter = ReporterFactory.create(_signal=signal)
        signal.reporter = new_reporter
        signal.save()

        update_reporter.send(sender=self.__class__,
                             signal_obj=signal,
                             reporter=new_reporter,
                             prev_reporter=prev_reporter)

        mocked_tasks.send_mail_apptimize.delay.assert_called_once_with(pk=signal.id)
