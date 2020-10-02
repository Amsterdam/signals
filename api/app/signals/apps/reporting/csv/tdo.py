import csv
import os
import tempfile
from typing import Callable

from signals.apps.reporting.csv.utils import queryset_to_csv_file, save_csv_files
from signals.apps.reporting.models import TDOSignal
from signals.apps.signals.workflow import LEEG, STATUS_CHOICES
from signals.celery import app


def create_signals_csv(location: str) -> str:
    """
    Create the CSV file based on the Signals view

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    queryset = TDOSignal.objects.all().order_by('id')
    csv_file = queryset_to_csv_file(queryset, os.path.join(location, 'signals.csv'))
    return csv_file.name


def create_statuses_csv(location: str) -> str:
    """
    Create the CSV file based on the STATUS_CHOICES from the workflow.py

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'statuses.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['code', 'name'])
        writer.writerow([LEEG, 'Leeg'])  # Special case, not present in STATUS_CHOICES
        for row in STATUS_CHOICES:
            writer.writerow(row)
    return csv_file.name


@app.task
def save_csv_file_tdo(func: Callable[[str], str]) -> None:
    """
    Create CSV files for teamdata openbare ruimte and save them on the storage backend.

    :returns:
    """
    csv_files = list()
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            csv_files.append(func(tmp_dir))
        except EnvironmentError:
            pass

        # Store the CSV files to the correct location
        save_csv_files(csv_files=csv_files, using='tdo', path='SIA/')
