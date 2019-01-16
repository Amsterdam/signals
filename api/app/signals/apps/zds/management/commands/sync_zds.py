import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from signals.apps.signals.models import Signal
from signals.apps.zds.exceptions import (
    CaseConnectionException,
    CaseNotCreatedException,
    DocumentConnectionException,
    DocumentNotCreatedException,
    StatusNotCreatedException
)
from signals.apps.zds.tasks import (
    add_document_to_case,
    add_status_to_case,
    connect_signal_to_case,
    create_case,
    create_document
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync the signals with the ZDS components"

    def handle(self, *args, **options):
        """
        Only select the signals that are 10 minutes old.
        Select signals that have no case or have not been done syncing.
        """
        ten_minutes_ago = timezone.now() - timedelta(seconds=600)
        signals_id1 = list(Signal.objects.filter(case__isnull=True).values_list('pk', flat=True))
        signals_id2 = list(Signal.objects.filter(case__isnull=False).filter(
            case__sync_completed=False).values_list('pk', flat=True))
        signal_ids = signals_id1 + signals_id2

        signals = Signal.objects.filter(pk__in=signal_ids, created_at__lte=ten_minutes_ago)
        for signal in signals:
            self.sync_case(signal)

    def sync_case(self, signal):
        """
        Push the case to the ZDS components.
        If the case already exists, it will continue to connect the signal to the case.

        If everything went correctly, continue to add the statusses to the ZDS components.
        """
        try:
            create_case(signal)

            try:
                connect_signal_to_case(signal)
                self.sync_status(signal)
            except CaseConnectionException as case_exception:
                logger.exception(case_exception)
                self.stderr.write(repr(case_exception))
        except CaseNotCreatedException as case_exception:
            logger.exception(case_exception)
            self.stderr.write(repr(case_exception))

    def sync_status(self, signal):
        """
        Push all the statusses that are connected to the signal to the ZDS components.
        If a status already exists, it will skip the status and continue with the other statusses.

        If everything went correctly, continue to add the documents to the ZDS components.
        """
        try:
            for status in signal.statuses.order_by('created_at'):
                add_status_to_case(signal, status)

            self.sync_document(signal)
        except StatusNotCreatedException as status_exception:
            logger.exception(status_exception)
            self.stderr.write(repr(status_exception))

    def sync_document(self, signal):
        """
        Push all the images that are connected to the signal to the ZDS components.
        If the document already exists, set signal sync to completed.
        """
        if signal.image:
            try:
                case_document = create_document(signal)

                try:
                    add_document_to_case(signal, case_document)
                    signal.case.sync_completed = True
                    signal.case.save()
                except DocumentConnectionException as document_exception:
                    logger.exception(document_exception)
                    self.stderr.write(repr(document_exception))
            except DocumentNotCreatedException as document_exception:
                logger.exception(document_exception)
                self.stderr.write(repr(document_exception))
