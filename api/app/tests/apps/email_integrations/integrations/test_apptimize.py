import json
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings

from signals.apps.email_integrations.integrations import apptimize
from tests.apps.signals.factories import SignalFactory


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
        ),
        'Afval': (
            ('F01', 'Afval', 'Veeg- / zwerfvuil', 'A3DEC', "CCA,ASC,STW"),
            ('F07', 'Afval', 'Prullenbak is vol', 'A3DEC', "CCA,ASC,STW"),
        ),
    }
)
class TestIntegrationApptimize(TestCase):

    @mock.patch('signals.apps.email_integrations.integrations.apptimize.is_signal_applicable',
                return_value=True, autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.apptimize.django_send_mail')
    def test_send_mail(self, mocked_django_send_mail, mocked_is_signal_applicable):
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

        apptimize.send_mail(signal)

        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False)

    @mock.patch('signals.apps.email_integrations.integrations.apptimize.is_signal_applicable',
                return_value=False, autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.apptimize.django_send_mail')
    def test_send_mail_not_applicable(self, mocked_django_send_mail, mocked_is_signal_applicable):
        signal = SignalFactory.create()

        apptimize.send_mail(signal)

        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_not_called()

    def test_is_signal_applicable_in_category(self):
        signal = SignalFactory.create(category__main='Openbaar groen en water',
                                      category__sub='Boom')

        result = apptimize.is_signal_applicable(signal)

        self.assertEqual(result, True)

    def test_is_signal_applicable_outside_category(self):
        signal = SignalFactory.create(category__main='Some other main category',
                                      category__sub='Some other sub category')

        result = apptimize.is_signal_applicable(signal)

        self.assertEqual(result, False)

    @override_settings(EMAIL_APPTIMIZE_INTEGRATION_ADDRESS=None)
    def test_is_signal_applicable_no_email(self):
        signal = SignalFactory.create(category__main='Openbaar groen en water',
                                      category__sub='Boom')

        result = apptimize.is_signal_applicable(signal)

        self.assertEqual(result, False)
