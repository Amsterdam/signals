import logging

from signals.celery import app
from signals.utils.datawarehouse import save_csv_files_datawarehouse

logger = logging.getLogger(__name__)


@app.task
def task_save_csv_files_datawarehouse():
    """Celery task to save CSV files for Datawarehouse.

    This task is scheduled in Celery beat to run periodically.

    :returns:
    """
    save_csv_files_datawarehouse()
