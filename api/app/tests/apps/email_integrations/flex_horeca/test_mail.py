from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase

from signals.apps.email_integrations.flex_horeca import mail as flex_horeca_mail
from tests.apps.signals.factories import SignalFactory


class TestIntegrationFlexHoreca(TestCase):
    def test_send_mail_integration_test(self):
        signal = SignalFactory.create(
            category_assignment__category__parent__name='Overlast Bedrijven en Horeca',
            category_assignment__category__name='Geluidsoverlast muziek')

        number_of_messages = flex_horeca_mail.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Nieuwe melding op meldingen.amsterdam.nl')

    @mock.patch('signals.apps.email_integrations.flex_horeca.mail.django_send_mail',
                return_value=1, autospec=True)
    @mock.patch('signals.apps.email_integrations.flex_horeca.mail.'
                'create_default_notification_message', autospec=True)
    def test_send_mail(self, mocked_create_default_notification_message, mocked_django_send_mail):
        mocked_message = mock.Mock()
        mocked_create_default_notification_message.return_value = mocked_message

        signal = SignalFactory.create()
        number_of_messages = flex_horeca_mail.send_mail(signal)

        self.assertEqual(number_of_messages, 1)
        mocked_django_send_mail.assert_called_once_with(
            subject='Nieuwe melding op meldingen.amsterdam.nl',
            message=mocked_message,
            from_email=settings.NOREPLY,
            recipient_list=['test@test.com', ])
