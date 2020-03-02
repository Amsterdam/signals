from django.db.models import Q
from django.test import TransactionTestCase
from django.utils import timezone
from freezegun import freeze_time

from signals.apps.signals.models import Reporter
from signals.apps.signals.tasks import anonymize_reporter, anonymize_reporters
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    BEHANDELING,
    GEANNULEERD,
    GESPLITST,
    VERZOEK_TOT_AFHANDELING
)
from tests.apps.signals.factories import SignalFactory


class TestTaskTranslateCategory(TransactionTestCase):
    def test_anonymize_reporter(self):
        signal = SignalFactory.create(status__state=AFGEHANDELD)
        reporter = signal.reporter

        self.assertIsNotNone(reporter.email)
        self.assertIsNotNone(reporter.phone)
        self.assertFalse(reporter.email_anonymized)
        self.assertFalse(reporter.phone_anonymized)

        anonymize_reporter(reporter_id=reporter.pk)

        reporter.refresh_from_db()

        self.assertIsNone(reporter.email)
        self.assertIsNone(reporter.phone)
        self.assertTrue(reporter.email_anonymized)
        self.assertTrue(reporter.phone_anonymized)

    def test_anonymize_reporters(self):
        allowed_states = [AFGEHANDELD, GEANNULEERD, GESPLITST, VERZOEK_TOT_AFHANDELING]
        with freeze_time(timezone.now() - timezone.timedelta(days=1)):
            for allowed_state in allowed_states:
                SignalFactory.create(status__state=allowed_state)

        self.assertEqual(Reporter.objects.count(), 4)

        anonymize_reporters(days=1)

        self.assertEqual(Reporter.objects.count(), 4)
        self.assertEqual(Reporter.objects.filter(Q(email_anonymized=True) | Q(phone_anonymized=True)).count(), 4)

        for reporter in Reporter.objects.all():
            self.assertIsNone(reporter.email)
            self.assertIsNone(reporter.phone)
            self.assertTrue(reporter.email_anonymized)
            self.assertTrue(reporter.phone_anonymized)

    def test_anonymize_reporters_less_than_x_days_ago(self):
        allowed_states = [AFGEHANDELD, GEANNULEERD, GESPLITST, VERZOEK_TOT_AFHANDELING]
        with freeze_time(timezone.now() - timezone.timedelta(days=1)):
            for allowed_state in allowed_states:
                SignalFactory.create(status__state=allowed_state)

        self.assertEqual(Reporter.objects.count(), 4)

        anonymize_reporters(days=2)

        self.assertEqual(Reporter.objects.count(), 4)
        self.assertEqual(Reporter.objects.filter(Q(email_anonymized=True) | Q(phone_anonymized=True)).count(), 0)
        self.assertEqual(Reporter.objects.filter(email_anonymized=False, phone_anonymized=False).count(), 4)

        for reporter in Reporter.objects.all():
            self.assertIsNotNone(reporter.email)
            self.assertIsNotNone(reporter.phone)
            self.assertFalse(reporter.email_anonymized)
            self.assertFalse(reporter.phone_anonymized)

    def test_anonymize_reporters_not_in_correct_state(self):
        with freeze_time(timezone.now() - timezone.timedelta(days=1)):
            SignalFactory.create_batch(5, status__state=BEHANDELING)

        self.assertEqual(Reporter.objects.count(), 5)

        anonymize_reporters(days=1)

        self.assertEqual(Reporter.objects.count(), 5)
        self.assertEqual(Reporter.objects.filter(Q(email_anonymized=True) | Q(phone_anonymized=True)).count(), 0)
        self.assertEqual(Reporter.objects.filter(email_anonymized=False, phone_anonymized=False).count(), 5)

        for reporter in Reporter.objects.all():
            self.assertIsNotNone(reporter.email)
            self.assertIsNotNone(reporter.phone)
            self.assertFalse(reporter.email_anonymized)
            self.assertFalse(reporter.phone_anonymized)

    def test_anonymize_reporters_multiple_cases(self):
        with freeze_time(timezone.now() - timezone.timedelta(days=1)):
            SignalFactory.create(status__state=AFGEHANDELD)

        with freeze_time(timezone.now() - timezone.timedelta(days=1)):
            SignalFactory.create(status__state=BEHANDELING)

        with freeze_time(timezone.now() - timezone.timedelta(days=2)):
            SignalFactory.create(status__state=BEHANDELING)

        with freeze_time(timezone.now() - timezone.timedelta(days=2)):
            SignalFactory.create(status__state=GESPLITST)

        with freeze_time(timezone.now() - timezone.timedelta(days=3)):
            SignalFactory.create(status__state=VERZOEK_TOT_AFHANDELING)

        with freeze_time(timezone.now() - timezone.timedelta(days=3)):
            SignalFactory.create(status__state=BEHANDELING)

        with freeze_time(timezone.now() - timezone.timedelta(days=4)):
            SignalFactory.create(status__state=GEANNULEERD)

        self.assertEqual(Reporter.objects.count(), 7)

        anonymize_reporters(days=2)
        self.assertEqual(Reporter.objects.filter(Q(email_anonymized=True) | Q(phone_anonymized=True)).count(), 3)
        self.assertEqual(Reporter.objects.filter(email_anonymized=False, phone_anonymized=False).count(), 4)

        self.assertEqual(Reporter.objects.count(), 7)
