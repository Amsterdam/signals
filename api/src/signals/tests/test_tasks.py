import json
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings

import signals.integrations.apptimize.handler
from signals import tasks
from signals.tests.factories import SignalFactory


class TestTaskSendToApptimize(TestCase):

    @mock.patch('signals.tasks.send_mail')
    @mock.patch('signals.tasks._is_signal_applicable_for_apptimize',
                return_value=True)
    def test_send_mail_apptimize(
            self, mocked_is_signal_applicable_for_apptimize, mocked_send_mail):
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
                'hoofdrubriek': signal.category.main,
                'subrubriek': signal.category.sub,
            },
            'omschrijving': signal.text,
        }, indent=4, sort_keys=True, default=str)

        tasks.send_mail_apptimize(key=signal.id)

        mocked_is_signal_applicable_for_apptimize.assert_called_once_with(
            signal)
        mocked_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False)

    @mock.patch('signals.tasks.send_mail')
    @mock.patch('signals.tasks.log')
    def test_send_mail_apptimize_no_signal_found(
            self, mocked_log, mocked_send_mail):
        tasks.send_mail_apptimize(key=1)  # id `1` shouldn't be found.

        mocked_log.exception.assert_called_once()
        mocked_send_mail.assert_not_called()

    @mock.patch('signals.tasks.send_mail')
    @mock.patch('signals.tasks._is_signal_applicable_for_apptimize',
                return_value=False)
    def test_send_mail_apptimize_not_applicable(
            self, mocked_is_signal_applicable_for_apptimize, mocked_send_mail):
        signal = SignalFactory.create()

        tasks.send_mail_apptimize(key=signal.id)

        mocked_is_signal_applicable_for_apptimize.assert_called_once_with(
            signal)
        mocked_send_mail.assert_not_called()


@override_settings(
    EMAIL_APPTIMIZE_INTEGRATION_ADDRESS='test@test.com',
    SUB_CATEGORIES_DICT={
        # Sample snippet of `SUB_CATEGORIES_DICT` from settings.
        'Openbaar groen en water': (
            ('F41', 'Openbaar groen en water', 'Boom', 'I5DMC', 'CCA,ASC,STW'),
            ('F42', 'Openbaar groen en water', 'Maaien / snoeien', 'I5DMC',
             'CCA,ASC,STW'),
            # ...
        ),
        'Wegen, verkeer, straatmeubilair': (
            ('F14', 'Wegen, verkeer, straatmeubilair',
             'Onderhoud stoep, straat en fietspad', 'A3DEC', 'CCA,ASC,STW'),
            ('F15', 'Wegen, verkeer, straatmeubilair',
             'Verkeersbord, verkeersafzetting', 'A3DEC', 'CCA,ASC,STW'),
            # ...
        )
    }
)
class TestHelperIsSignalApplicableForApptimize(TestCase):

    def test_is_signal_applicable_for_apptimize_in_category(self):
        signal = SignalFactory.create(
            category__main='Openbaar groen en water',
            category__sub='Boom')

        result = signals.integrations.apptimize.handler.is_signal_applicable(signal)

        self.assertEqual(result, True)

    def test_is_signal_applicable_for_apptimize_outside_category(self):
        signal = SignalFactory.create(
            category__main='Some other main category',
            category__sub='Some other sub category')

        result = signals.integrations.apptimize.handler.is_signal_applicable(signal)

        self.assertEqual(result, False)

    @override_settings(EMAIL_APPTIMIZE_INTEGRATION_ADDRESS=None)
    def test_is_signal_applicable_for_apptimize_no_email(self):
        signal = SignalFactory.create(
            category__main='Openbaar groen en water',
            category__sub='Boom')

        result = signals.integrations.apptimize.handler.is_signal_applicable(signal)

        self.assertEqual(result, False)
