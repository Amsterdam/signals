import tempfile
from typing import Callable

from signals.apps.reporting.csv.datawarehouse.categories import (
    create_category_assignments_csv,
    create_category_sla_csv
)
from signals.apps.reporting.csv.datawarehouse.kto_feedback import create_kto_feedback_csv
from signals.apps.reporting.csv.datawarehouse.locations import create_locations_csv
from signals.apps.reporting.csv.datawarehouse.reporters import create_reporters_csv
from signals.apps.reporting.csv.datawarehouse.signals import create_signals_csv
from signals.apps.reporting.csv.datawarehouse.statusses import create_statuses_csv
from signals.apps.reporting.csv.datawarehouse.utils import save_csv_files


def save_csv_file_datawarehouse(func: Callable[[str], str]) -> None:
    """
    Create CSV files for Datawarehouse and save them on the storage backend.

    :returns:
    """
    csv_files = list()
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            csv_files.append(func(tmp_dir))
        except EnvironmentError:
            pass

        # Store the CSV files to the correct location
        save_csv_files(csv_files)


def save_csv_files_datawarehouse():
    """
    Create CSV files for Datawarehouse and save them on the storage backend.

    :returns:
    """
    save_csv_file_datawarehouse(create_signals_csv)
    save_csv_file_datawarehouse(create_locations_csv)
    save_csv_file_datawarehouse(create_reporters_csv)
    save_csv_file_datawarehouse(create_category_assignments_csv)
    save_csv_file_datawarehouse(create_statuses_csv)
    save_csv_file_datawarehouse(create_category_sla_csv)

    try:
        save_csv_file_datawarehouse(create_kto_feedback_csv)
    except EnvironmentError:
        pass
