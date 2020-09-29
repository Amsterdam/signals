import tempfile
from typing import Callable

from signals.apps.reporting.csv.utils import save_csv_files
from signals.celery import app


def create_signals_csv(location: str) -> str:
    """
    Create the CSV file based on the Signals view

    TODO: Add functionality to export the "view" to CSV, for an example look at the datawarehouse/signals.py file

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    pass


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
        save_csv_files(csv_files=csv_files, using='tdo')
