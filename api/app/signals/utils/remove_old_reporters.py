import logging
from datetime import timezone

from django.utils.datetime_safe import datetime

from signals.apps.signals.models import Reporter

log = logging.getLogger(__name__)


def remove_old_reporters():
    """
    Remove all reporters where the remove_at timestamp is past due
    """
    old_reporters = Reporter.objects.filter(remove_at__lt=datetime.now(timezone.utc))

    delete_count = 0
    for old_reporter in old_reporters:
        old_reporter.delete()
        delete_count += 1
    log.warning(f"Removed {delete_count} old reporters")
