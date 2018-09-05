from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from freezegun import freeze_time

from signals.apps.email_integrations.integrations import flex_horeca
from tests.apps.signals.factories import SignalFactory


@override_settings(
    EMAIL_FLEX_HORECA_INTEGRATION_ADDRESS='test@test.com',
    SUB_CATEGORIES_DICT={
        # Sample snippet of `SUB_CATEGORIES_DICT` from settings.
        'Overlast Bedrijven en Horeca': (
            ('F63', 'Overlast Bedrijven en Horeca', 'Geluidsoverlast muziek', 'I5DMC',
             'CCA,ASC,VTH'),
            ('F64', 'Overlast Bedrijven en Horeca', 'Geluidsoverlast installaties', 'I5DMC',
             'CCA,ASC,VTH'),
            ('F65', 'Overlast Bedrijven en Horeca', 'Overlast terrassen', 'I5DMC', 'CCA,ASC,VTH'),
            # ...
        ),
    }
)
class TestIntegrationFlexHoreca(TestCase):

    @freeze_time('2018-08-03')  # Friday
    def test_send_mail_integration_test(self):
        """Integration test for `send_mail` function."""
        signal = SignalFactory.create(category__main='Overlast Bedrijven en Horeca',
                                      category__sub='Geluidsoverlast muziek')

        number_of_messages = flex_horeca.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Nieuwe melding op meldingen.amsterdam.nl')

    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.django_send_mail',
                return_value=1, autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.loader', autospec=True)
    @mock.patch('signals.apps.email_integrations.integrations.flex_horeca.is_signal_applicable',
                return_value=True, autospec=True)
    def test_send_mail(self, mocked_is_signal_applicable, mocked_loader, mocked_django_send_mail):
        # Setting up template mocking.
        mocked_rendered_template = mock.Mock()
        mocked_template = mock.Mock()
        mocked_template.render.return_value = mocked_rendered_template
        mocked_loader.get_template.return_value = mocked_template

        # Creating a `Signal` object to use for sending mail to Flex Horeca.
        signal = SignalFactory.create()
        number_of_messages = flex_horeca.send_mail(signal)

        # Asserting all correct function calls.
        mocked_loader.get_template.assert_called_once_with('email/flex_horeca.txt')
        mocked_template.render.assert_called_once_with({'signal': signal})

        self.assertEqual(number_of_messages, 1)
        mocked_is_signal_applicable.assert_called_once_with(signal)
        mocked_django_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=mocked_rendered_template,
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
        signal = SignalFactory.create(category__main='Overlast Bedrijven en Horeca',
                                      category__sub='Geluidsoverlast muziek')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-04')  # Saterday
    def test_is_signal_applicable_in_category_on_saterday(self):
        signal = SignalFactory.create(category__main='Overlast Bedrijven en Horeca',
                                      category__sub='Geluidsoverlast muziek')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, True)

    @freeze_time('2018-08-03')  # Friday
    def test_is_signal_applicable_outside_category_on_friday(self):
        signal = SignalFactory.create(category__main='Some other main category',
                                      category__sub='Some other sub category')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, False)

    @freeze_time('2018-08-05')  # Sunday
    def test_is_signal_applicable_in_category_on_sunday(self):
        signal = SignalFactory.create(category__main='Overlast Bedrijven en Horeca',
                                      category__sub='Geluidsoverlast muziek')

        result = flex_horeca.is_signal_applicable(signal)

        self.assertEqual(result, False)
