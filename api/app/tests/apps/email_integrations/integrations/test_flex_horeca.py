from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from freezegun import freeze_time

from signals.apps.email_integrations.integrations import flex_horeca
from tests.apps.signals.factories import SignalFactory


@override_settings(
    EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS='test@test.com',
    EMAIL_FLEX_HORECA_WEEKDAYS='5,6,7',  # friday, saterday, sunday
    EMAIL_FLEX_HORECA_END_TIME='04:00',
)
class TestIntegrationFlexHoreca(TestCase):

    @freeze_time('2018-08-03')  # Friday
    def test_send_mail_integration_test(self):
        """Integration test for `send_mail` function."""
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Overlast Bedrijven en Horeca',
            category_assignment__sub_category__name='Geluidsoverlast muziek')

        number_of_messages = flex_horeca.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Nieuwe melding op meldingen.amsterdam.nl')

    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.django_send_mail',
                return_value=1, autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.'
                'create_default_notification_message', autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.is_signal_applicable',
                return_value=True, autospec=True)
    def test_send_mail(
            self,
            mocked_is_signal_applicable,
            mocked_create_default_notification_message,
            mocked_django_send_mail):
        # Setting up mocked notification message.
        mocked_message = mock.Mock()
        mocked_create_default_notification_message.return_value = mocked_message

        signal = SignalFactory.create()
        number_of_messages = flex_horeca.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=mocked_message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS, ))

    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.django_send_mail',
                autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.is_signal_applicable',
                return_value=False, autospec=True)
    def test_send_mail_not_applicable(self, mocked_is_signal_applicable, mocked_django_send_mail):
        signal = SignalFactory.create()

        number_of_messages = flex_horeca.send_mail(signal)

        self.assertEqual(number_of_messages, 0)
        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_not_called()

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_in_category_on_friday(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Overlast Bedrijven en Horeca',
            category_assignment__sub_category__name='Geluidsoverlast muziek')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-05 01:00:00')  # Sunday 01:00
    def test_is_signal_applicable_in_category_on_sunday_before_end_time(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Overlast Bedrijven en Horeca',
            category_assignment__sub_category__name='Geluidsoverlast muziek')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_outside_category_on_friday(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Some other main category',
            category_assignment__sub_category__name='Some other sub category')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, False)

    @freeze_time('2018-08-05 05:00:00')  # Sunday 05:00
    def test_is_signal_applicable_in_category_on_sunday_after_end_time(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Overlast Bedrijven en Horeca',
            category_assignment__sub_category__name='Geluidsoverlast muziek')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, False)
