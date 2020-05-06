import logging

from django.db.models import Q
from django.utils import timezone

from signals.apps.signals.models import Reporter
from signals.apps.signals.models.category_translation import CategoryTranslation
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    GEANNULEERD,
    GESPLITST,
    VERZOEK_TOT_AFHANDELING
)
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def translate_category(signal_id):
    signal = Signal.objects.get(pk=signal_id)

    current_category = signal.category_assignment.category
    try:
        trans = CategoryTranslation.objects.get(old_category=current_category)
    except CategoryTranslation.DoesNotExist:
        return  # no need to perform a category re-assignment

    data = {
        'category': trans.new_category,
        'text': trans.text,
        'created_by': None,  # This wil show as "SIA systeem"
    }

    Signal.actions.update_category_assignment(data, signal)


@app.task
def anonymize_reporters(days=365):
    created_before = (timezone.now() - timezone.timedelta(days=days))
    allowed_signal_states = [AFGEHANDELD, GEANNULEERD, GESPLITST, VERZOEK_TOT_AFHANDELING]

    reporter_ids = Reporter.objects.filter(
        Q(email__isnull=False) & ~Q(email__exact=''),
        Q(phone__isnull=False) & ~Q(phone__exact=''),
        email_anonymized=False,
        phone_anonymized=False,
        created_at__lt=created_before,
        _signal__status__state__in=allowed_signal_states,
    ).values_list(
        'pk', flat=True
    )

    reporter_count = reporter_ids.count()

    for reporter_id in reporter_ids:
        anonymize_reporter.delay(reporter_id=reporter_id)

    return reporter_count


@app.task
def anonymize_reporter(reporter_id):
    try:
        reporter = Reporter.objects.get(pk=reporter_id)
    except Reporter.DoesNotExist:
        log.warning(f"Reporter with ID #{reporter_id} does not exists")
    else:
        if reporter.is_anonymous:
            # The reporter is anonymous so no need to anonymize it
            return

        if not reporter.is_anonymized:
            reporter.anonymize()

            changed = []
            if reporter.email_anonymized:
                changed.append('email')
            if reporter.phone_anonymized:
                changed.append('telefoonnummer')
            text = 'Vanwege de AVG zijn de volgende gegevens van de melder ' \
                   'geanonimiseerd: {}'.format(', '.join(changed))

            Signal.actions.create_note(data={
                'text': text,
                'created_by': None  # This wil show as "SIA systeem"
            }, signal=reporter.signal)
