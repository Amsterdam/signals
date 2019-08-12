from datetime import timedelta

from django.test import TransactionTestCase
from django.utils import timezone

from signals.apps.signals.models import Reporter
from signals.utils.remove_old_reporters import remove_old_reporters
from tests.apps.signals.factories import ReporterFactory


class TestRemoveOldReporters(TransactionTestCase):
    def setUp(self):
        ReporterFactory.create_batch(5)

        yesterday = timezone.now() - timedelta(days=1)
        self.reporters = ReporterFactory.create_batch(5, remove_at=yesterday)

    def test_command(self):
        remove_old_reporters()

        self.assertEqual(5, Reporter.objects.count())
        qs = Reporter.objects.filter(pk__in=[
            removed_reporter.id for removed_reporter in self.reporters
        ])
        self.assertFalse(qs.exists())
