"""
Periodic tasks for reporting
"""
import logging

from signals.apps.reporting.csv.datawarehouse import (
    save_csv_files_datawarehouse,
    save_csv_files_endpoint
)
from signals.celery import app

logger = logging.getLogger(__name__)


@app.task
def task_save_csv_files_datawarehouse():
    """Celery task to save CSV files for Datawarehouse.

    This task is scheduled in Celery beat to run periodically.

    :returns:
    """
    save_csv_files_datawarehouse()


@app.task
def task_save_csv_files_endpoint():
    """Celery task to save CSV files for csv endpoint
    This task is scheduled in Celery beat to run periodically.

    :returns:
    """
    save_csv_files_endpoint()
