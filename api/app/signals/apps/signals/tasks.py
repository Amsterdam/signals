import logging
from typing import Optional

from signals.apps.signals.models import Signal
from signals.celery import app
from signals.utils.datawarehouse import save_csv_files_datawarehouse

logger = logging.getLogger(__name__)


def retrieve_signal(pk: int) -> Optional[Signal]:
    try:
        signal = Signal.objects.get(id=pk)
    except Signal.DoesNotExist as e:
        logger.exception(str(e))
        return None
    return signal


@app.task
def task_save_csv_files_datawarehouse():
    """Celery task to save CSV files for Datawarehouse.

    This task is scheduled in Celery beat to run periodically.

    :returns:
    """
    save_csv_files_datawarehouse()
