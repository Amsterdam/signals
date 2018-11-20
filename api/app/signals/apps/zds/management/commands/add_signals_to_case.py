import logging

from django.core.management.base import BaseCommand
from zds_client import ClientError

from signals.apps.signals.models import Signal
from signals.apps.signals.workflow import ZTC_STATUSSES
from signals.apps.zds import zds_client
from signals.apps.zds.exceptions import StatusNotCreatedException
from signals.apps.zds.tasks import (
    add_document_to_case,
    connect_signal_to_case,
    create_case,
    create_document
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        signals = Signal.objects.filter(zaak__isnull=True)
        for signal in signals:
            self.create_case(signal)

    def create_case(self, signal):
        try:
            create_case(signal)
            connect_signal_to_case(signal)
            create_document(signal)
            add_document_to_case(signal)

            for status in signal.statuses.order_by('created_at'):
                # This is done custom so we can add all statusses
                data = {
                    'zaak': signal.zaak.zrc_link,
                    'statusType': ZTC_STATUSSES.get(status.state),
                    'datumStatusGezet': status.created_at.isoformat(),
                }

                try:
                    zds_client.zrc.create('status', data)
                except (ClientError, ConnectionError) as error:
                    logger.exception(error)
                    raise StatusNotCreatedException()
        except Exception as e:
            logger.exception(e)
