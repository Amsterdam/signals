# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2018 - 2023 Gemeente Amsterdam
import logging

from django.core.management import call_command
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from signals.apps.services.domain.auto_create_children.service import AutoCreateChildrenService
from signals.apps.services.domain.delete_signals import SignalDeletionService
from signals.apps.services.domain.dsl import SignalDslService
from signals.apps.signals.models import Reporter
from signals.apps.signals.models.signal import Signal
from signals.apps.signals.workflow import (
    AFGEHANDELD,
    GEANNULEERD,
    GESPLITST,
    VERZOEK_TOT_AFHANDELING
)
from signals.celery import app

log = logging.getLogger(__name__)
dsl_service = SignalDslService()


@app.task
def apply_routing(signal_id):
    signal = Signal.objects.get(pk=signal_id)
    dsl_service.process_routing_rules(signal)


@app.task
def anonymize_reporters(days=365):
    created_before = (timezone.now() - timezone.timedelta(days=days))
    allowed_signal_states = [AFGEHANDELD, GEANNULEERD, GESPLITST, VERZOEK_TOT_AFHANDELING]

    reporter_ids = Reporter.objects.filter(
        (Q(email__isnull=False) & ~Q(email__exact='')) | (Q(phone__isnull=False) & ~Q(phone__exact='')),
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


@app.task
def update_status_children_based_on_parent(signal_id):
    signal = Signal.objects.get(pk=signal_id)
    if signal.is_parent and signal.status.state in [AFGEHANDELD, GEANNULEERD, ]:
        text = 'Hoofdmelding is afgehandeld'

        # Lets check the children
        children = signal.children.exclude(status__state__in=[AFGEHANDELD, GEANNULEERD, ])
        for child in children:
            # All children must get the state "GEANNULEERD"
            data = dict(state=GEANNULEERD, text=text)
            Signal.actions.update_status(data=data, signal=child)


@app.task
def apply_auto_create_children(signal_id):
    """
    !!! This will be refactored when the "uitvraag" will be moved to the API !!!

    :param signal_id:
    """
    AutoCreateChildrenService.run(signal_id=signal_id)


@app.task
def delete_closed_signals(days=365):
    """
    Delete Signals in one of the Signalen system's closed states
    """
    SignalDeletionService.delete_signals(AFGEHANDELD, days, dry_run=False)
    SignalDeletionService().delete_signals(GEANNULEERD, days, dry_run=False)
    SignalDeletionService().delete_signals(GESPLITST, days, dry_run=False)


@app.task
def refresh_materialized_view_public_signals_geography_feature_collection():
    """
    A task to refresh the materialized view that contains the data for the public/v1/signals/geography endpoint
    """
    refresh_query = 'REFRESH MATERIALIZED VIEW CONCURRENTLY "public_signals_geography_feature_collection";'

    cursor = connection.cursor()
    try:
        cursor.execute(refresh_query)
    except Exception as e:
        log.error(f'Failed to execute the query: {refresh_query}', exc_info=e)
    finally:
        cursor.close()


@app.task
def clearsessions():
    """
    This task makes it possible to configure the "clearsession" management command through Celery
    """
    call_command('clearsessions')
