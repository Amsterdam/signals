import json
from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from signals.apps.email_integrations.integrations import apptimize
from tests.apps.signals.factories import SignalFactory


@override_settings(EMAIL_APPTIMIZE_INTEGRATION_ADDRESS='test@test.com')
class TestIntegrationApptimize(TestCase):

    def test_send_mail_integration_test(self):
        """Integration test for `send_mail` function."""
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Openbaar groen en water',
            category_assignment__sub_category__name='Boom')

        number_of_messages = apptimize.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Nieuwe melding op meldingen.amsterdam.nl')

    @mock.patch('signals.apps.email_integrations.integrations.apptimize.django_send_mail',
                return_value=1, autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.apptimize.is_signal_applicable',
                return_value=True, autospec=True)
    def test_send_mail(self, mocked_is_signal_applicable, mocked_django_send_mail):
        signal = SignalFactory.create()
        message = json.dumps({
            'mora_nummer': signal.id,
            'signal_id': signal.signal_id,
            'tijdstip': signal.incident_date_start,
            'email_melder': signal.reporter.email,
            'telefoonnummer_melder': signal.reporter.phone,
            'adres': signal.location.address,
            'stadsdeel': signal.location.stadsdeel,
            'categorie': {
                'hoofdrubriek': signal.category_assignment.sub_category.main_category.name,
                'subrubriek': signal.category_assignment.sub_category.name,
            },
            'omschrijving': signal.text,
        }, indent=4, sort_keys=True, default=str)

        number_of_messages = apptimize.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ))

    @mock.patch('signals.apps.email_integrations.integrations.apptimize.django_send_mail',
                autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.apptimize.is_signal_applicable',
                return_value=False, autospec=True)
    def test_send_mail_not_applicable(self, mocked_is_signal_applicable, mocked_django_send_mail):
        signal = SignalFactory.create()

        number_of_messages = apptimize.send_mail(signal)

        self.assertEqual(number_of_messages, 0)
        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_not_called()

    def test_is_signal_applicable_in_category(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Openbaar groen en water',
            category_assignment__sub_category__name='Boom')

        result = apptimize.is_signal_applicable(signal)

        self.assertEqual(result, True)

    def test_is_signal_applicable_outside_category(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Some other main category',
            category_assignment__sub_category__name='Some other sub category')

        result = apptimize.is_signal_applicable(signal)

        self.assertEqual(result, False)

    @override_settings(EMAIL_APPTIMIZE_INTEGRATION_ADDRESS=None)
    def test_is_signal_applicable_no_email(self):
        signal = SignalFactory.create(
            category_assignment__sub_category__main_category__name='Openbaar groen en water',
            category_assignment__sub_category__name='Boom')

        result = apptimize.is_signal_applicable(signal)

        self.assertEqual(result, False)
