import json
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from freezegun import freeze_time

import signals.integrations.apptimize.handler
from signals.apps.signals import tasks
from tests.factories import SignalFactory


class TestTaskSendMailApptimize(TestCase):
    @mock.patch('signals.integrations.apptimize.handler.is_signal_applicable',
                return_value=True)
    @mock.patch('signals.integrations.apptimize.handler.send_mail')
    def test_send_mail_apptimize(
            self, mocked_send_mail, mocked_is_signal_applicable):
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

        tasks.send_mail_apptimize(pk=signal.id)

        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_send_mail.assert_called_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=message,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False)

    @mock.patch('signals.integrations.apptimize.handler.handle')
    @mock.patch('signals.apps.signals.tasks.log')
    def test_send_mail_apptimize_no_signal_found(
            self, mocked_log, mocked_handle):
        tasks.send_mail_apptimize(pk=1)  # id `1` shouldn't be found.

        mocked_log.exception.assert_called_once()
        mocked_handle.assert_not_called()

    @mock.patch('signals.integrations.apptimize.handler.is_signal_applicable',
                return_value=False)
    @mock.patch('signals.integrations.apptimize.handler.handle')
    def test_send_mail_apptimize_not_applicable(
            self, mocked_handle, mocked_is_signal_applicable):
        signal = SignalFactory.create()

        tasks.send_mail_apptimize(pk=signal.id)

        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_handle.assert_not_called()


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


class TestTaskSendMailFlexHoreca(TestCase):

    @mock.patch('signals.apps.signals.tasks.send_mail')
    @mock.patch('signals.apps.signals.tasks.loader')
    @mock.patch('signals.apps.signals.tasks.'
                '_is_signal_applicable_for_flex_horeca',
                return_value=True)
    def test_send_mail_flex_horeca(
            self,
            mocked_is_signal_applicable_for_flex_horeca,
            mocked_loader,
            mocked_send_mail):
        # Setting up template mocking.
        mocked_rendered_template = mock.Mock()
        mocked_template = mock.Mock()
        mocked_template.render.return_value = mocked_rendered_template
        mocked_loader.get_template.return_value = mocked_template

        # Creating a `Signal` object to use for sending mail to Flex Horeca.
        signal = SignalFactory.create()
        tasks.send_mail_flex_horeca(pk=signal.id)

        # Asserting all correct function calls.
        mocked_loader.get_template.assert_called_once_with(
            'mail_flex_horeca.txt')
        mocked_template.render.assert_called_once_with({'signal': signal})

        mocked_is_signal_applicable_for_flex_horeca.assert_called_once_with(
            signal)
        mocked_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=mocked_rendered_template,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False)

    @mock.patch('signals.apps.signals.tasks.send_mail')
    @mock.patch('signals.apps.signals.tasks.log')
    def test_send_mail_flex_horeca_no_signal_found(
            self, mocked_log, mocked_send_mail):
        tasks.send_mail_flex_horeca(pk=1)  # id `1` shouldn't be found.

        mocked_log.exception.assert_called_once()
        mocked_send_mail.assert_not_called()

    @mock.patch('signals.apps.signals.tasks.send_mail')
    @mock.patch('signals.apps.signals.tasks._is_signal_applicable_for_flex_horeca',
                return_value=False)
    def test_send_mail_flex_horeca_not_applicable(
            self,
            mocked_is_signal_applicable_for_flex_horeca,
            mocked_send_mail):
        signal = SignalFactory.create()

        tasks.send_mail_flex_horeca(pk=signal.id)

        mocked_is_signal_applicable_for_flex_horeca.assert_called_once_with(
            signal)
        mocked_send_mail.assert_not_called()


class TestHelperIsSignalApplicableForFlexHoreca(TestCase):

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_for_flex_horeca_in_category_on_friday(self):
        signal = SignalFactory.create(
            category__main='Overlast Bedrijven en Horeca',
            category__sub='Geluidsoverlast muziek')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-04')  # Saterday
    def test_is_signal_applicable_for_flex_horeca_in_category_on_saterday(
            self):
        signal = SignalFactory.create(
            category__main='Overlast Bedrijven en Horeca',
            category__sub='Geluidsoverlast muziek')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_for_flex_horeca_outside_category_on_friday(
            self):
        signal = SignalFactory.create(
            category__main='Some other main category',
            category__sub='Some other sub category')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, False)

    @freeze_time('2018-08-05')  # Sunday
    def test_is_signal_applicable_for_flex_horeca_in_category_on_sunday(
            self):
        signal = SignalFactory.create(
            category__main='Overlast Bedrijven en Horeca',
            category__sub='Geluidsoverlast muziek')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, False)


class TestTaskSendMailFlexHoreca(TestCase):

    @mock.patch('signals.apps.signals.tasks.send_mail')
    @mock.patch('signals.apps.signals.tasks.loader')
    @mock.patch('signals.apps.signals.tasks.'
                '_is_signal_applicable_for_flex_horeca',
                return_value=True)
    def test_send_mail_flex_horeca(
            self,
            mocked_is_signal_applicable_for_flex_horeca,
            mocked_loader,
            mocked_send_mail):
        # Setting up template mocking.
        mocked_rendered_template = mock.Mock()
        mocked_template = mock.Mock()
        mocked_template.render.return_value = mocked_rendered_template
        mocked_loader.get_template.return_value = mocked_template

        # Creating a `Signal` object to use for sending mail to Flex Horeca.
        signal = SignalFactory.create()
        tasks.send_mail_flex_horeca(pk=signal.id)

        # Asserting all correct function calls.
        mocked_loader.get_template.assert_called_once_with(
            'mail_flex_horeca.txt')
        mocked_template.render.assert_called_once_with({'signal': signal})

        mocked_is_signal_applicable_for_flex_horeca.assert_called_once_with(
            signal)
        mocked_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=mocked_rendered_template,
            from_email=settings.NOREPLY,
            recipient_list=(settings.EMAIL_APPTIMIZE_INTEGRATION_ADDRESS, ),
            fail_silently=False)

    @mock.patch('signals.apps.signals.tasks.send_mail')
    @mock.patch('signals.apps.signals.tasks.log')
    def test_send_mail_flex_horeca_no_signal_found(
            self, mocked_log, mocked_send_mail):
        tasks.send_mail_flex_horeca(pk=1)  # id `1` shouldn't be found.

        mocked_log.exception.assert_called_once()
        mocked_send_mail.assert_not_called()

    @mock.patch('signals.apps.signals.tasks.send_mail')
    @mock.patch('signals.apps.signals.tasks.'
                '_is_signal_applicable_for_flex_horeca',
                return_value=False)
    def test_send_mail_flex_horeca_not_applicable(
            self,
            mocked_is_signal_applicable_for_flex_horeca,
            mocked_send_mail):
        signal = SignalFactory.create()

        tasks.send_mail_flex_horeca(pk=signal.id)

        mocked_is_signal_applicable_for_flex_horeca.assert_called_once_with(
            signal)
        mocked_send_mail.assert_not_called()


class TestHelperIsSignalApplicableForFlexHoreca(TestCase):

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_for_flex_horeca_in_category_on_friday(self):
        signal = SignalFactory.create(
            category__main='Overlast Bedrijven en Horeca',
            category__sub='Geluidsoverlast muziek')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-04')  # Saterday
    def test_is_signal_applicable_for_flex_horeca_in_category_on_saterday(
            self):
        signal = SignalFactory.create(
            category__main='Overlast Bedrijven en Horeca',
            category__sub='Geluidsoverlast muziek')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_for_flex_horeca_outside_category_on_friday(
            self):
        signal = SignalFactory.create(
            category__main='Some other main category',
            category__sub='Some other sub category')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, False)

    @freeze_time('2018-08-05')  # Sunday
    def test_is_signal_applicable_for_flex_horeca_in_category_on_sunday(
            self):
        signal = SignalFactory.create(
            category__main='Overlast Bedrijven en Horeca',
            category__sub='Geluidsoverlast muziek')

        result = tasks._is_signal_applicable_for_flex_horeca(signal)

        self.assertEqual(result, False)


class TestTaskSaveCSVFilesDatawarehouse(TestCase):

    @mock.patch('signals.apps.signals.tasks.save_csv_files_datawarehouse')
    def test_task_save_csv_files_datawarehouse(
            self, mocked_save_csv_files_datawarehouse):
        tasks.task_save_csv_files_datawarehouse()

        mocked_save_csv_files_datawarehouse.assert_called_once()
