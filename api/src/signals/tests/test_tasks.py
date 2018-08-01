import json
from unittest import mock

from django.conf import settings
from django.test import TestCase

from signals.tasks import send_mail_apptimize
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

        send_mail_apptimize(id=signal.id)

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
        send_mail_apptimize(id=1)  # id `1` shouldn't be found.

        mocked_log.exception.assert_called_once()
        mocked_send_mail.assert_not_called()

    @mock.patch('signals.tasks.send_mail')
    @mock.patch('signals.tasks._is_signal_applicable_for_apptimize',
                return_value=False)
    def test_send_mail_apptimize_not_applicable(
            self, mocked_is_signal_applicable_for_apptimize, mocked_send_mail):
        signal = SignalFactory.create()

        send_mail_apptimize(id=signal.id)

        mocked_is_signal_applicable_for_apptimize.assert_called_once_with(
            signal)
        mocked_send_mail.assert_not_called()

    def test_is_signal_applicable_for_apptimize_true(self):
        pass

    def test_is_signal_applicable_for_apptimize_false(self):
        pass
