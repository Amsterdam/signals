from django.test import TestCase

from signals.apps.email_integrations.integrations import core
from tests.apps.signals.factories import SignalFactory


class TestCore(TestCase):

    def setUp(self):
        self.signal = SignalFactory.create(reporter__email='foo@bar.com')

    def test_get_valid_email(self):
        email = core.get_valid_email(self.signal)
        self.assertEqual(email, 'foo@bar.com')

    def test_get_valid_email_invalid(self):
        signal = SignalFactory.create(reporter__email='no-valid-email-address')
        email = core.get_valid_email(signal)
        self.assertEqual(email, None)

    def test_send_mail_reporter_created(self):
        pass

    def test_send_mail_reporter_status_changed(self):
        pass
