# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import tempfile
from typing import Callable

from signals.apps.reporting.csv.datawarehouse.categories import (
    create_category_assignments_csv,
    create_category_sla_csv
)
from signals.apps.reporting.csv.datawarehouse.directing_departments import (
    create_directing_departments_csv
)
from signals.apps.reporting.csv.datawarehouse.kto_feedback import create_kto_feedback_csv
from signals.apps.reporting.csv.datawarehouse.locations import create_locations_csv
from signals.apps.reporting.csv.datawarehouse.reporters import create_reporters_csv
from signals.apps.reporting.csv.datawarehouse.signals import (
    create_signals_assigned_user_csv,
    create_signals_csv,
    create_signals_routing_departments_csv
)
from signals.apps.reporting.csv.datawarehouse.statusses import create_statuses_csv
from signals.apps.reporting.csv.utils import rotate_zip_files, save_csv_files, zip_csv_files
from signals.celery import app


@app.task
def save_csv_file_datawarehouse(func: Callable[[str], str], using='datawarehouse') -> None:
    """
    Create CSV files for Datawarehouse and save them on the storage backend.

    :returns: list of csv files
    """
    csv_files = list()
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            csv_files.append(func(tmp_dir))
        except EnvironmentError:
            pass

        # Store the CSV files to the correct location
        return save_csv_files(csv_files=csv_files, using=using)


@app.task
def save_csv_files_datawarehouse(using='datawarehouse'):
    """
    Create CSV files for Datawarehouse and save them on the storage backend.

    :returns: list of csv files
    """
    csv_files = list()
    csv_files.extend(save_csv_file_datawarehouse(create_signals_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_signals_assigned_user_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_locations_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_reporters_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_category_assignments_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_statuses_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_category_sla_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_directing_departments_csv, using=using))
    csv_files.extend(save_csv_file_datawarehouse(create_signals_routing_departments_csv, using=using))

    try:
        csv_files.extend(save_csv_file_datawarehouse(create_kto_feedback_csv, using=using))
    except EnvironmentError:
        pass
    return csv_files


@app.task
def zip_csv_files_endpoint(files: list):
    """
    Create zip file of generated csv files

    :returns:
    """
    zip_csv_files(files_to_zip=files, using='datawarehouse')


@app.task
def save_and_zip_csv_files_endpoint(max_csv_amount: int = 30):
    """
    Create zip file of generated csv files

    :returns:
    """
    created_files = save_csv_files_datawarehouse(using=None)
    zip_csv_files(files_to_zip=created_files, using='datawarehouse')
    rotate_zip_files(using='datawarehouse', max_csv_amount=max_csv_amount)
