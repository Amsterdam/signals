import logging

from django.core.management.base import BaseCommand

from signals.apps.signals.models import Signal
from signals.apps.zds import zds_client
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
    create_document,
    get_status
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync the signals with the ZDS components"

    def handle(self, *args, **options):
        signals_id1 = list(Signal.objects.filter(case__isnull=True).values_list('pk', flat=True))
        signals_id2 = list(Signal.objects.filter(case__isnull=False).filter(case__sync_completed=False).values_list('pk', flat=True))
        signal_ids = signals_id1 + signals_id2
        signals = Signal.objects.filter(pk__in=signal_ids)
        for signal in signals:
            self.sync_case(signal)

    def sync_case(self, signal):
        try:
            create_case(signal)

            try:
                connect_signal_to_case(signal)

                try:
                    for status in signal.statuses.order_by('created_at'):
                        add_status_to_case(signal, status)

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
                except StatusNotCreatedException as status_exception:
                    logger.exception(status_exception)
                    self.stderr.write(repr(status_exception))
            except CaseConnectionException as case_exception:  #
                logger.exception(case_exception)  #
                self.stderr.write(repr(case_exception))  #
        except CaseNotCreatedException as case_exception:  #
            logger.exception(case_exception)  #
            self.stderr.write(repr(case_exception))  #
