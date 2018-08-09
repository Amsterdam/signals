import csv
import json
import os
import tempfile

from django.conf import settings
from swift.storage import SwiftStorage

from signals.models import Signal, Location, Reporter, Category, Status


def save_csv_files_datawarehouse():
    """Create CSV files for Datawarehouse and save them on the storage backend.

    :returns:
    """
    # Creating all CSV files.
    csv_files = list()
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_files.append(_create_signals_csv(tmp_dir))
        csv_files.append(_create_locations_csv(tmp_dir))
        csv_files.append(_create_reporters_csv(tmp_dir))
        csv_files.append(_create_categories_csv(tmp_dir))
        csv_files.append(_create_statuses_csv(tmp_dir))

        # Getting the storage backend and save all CSV files.
        storage = _get_storage_backend()
        for csv_file_path in csv_files:
            with open(csv_file_path, 'rb') as opened_csv_file:
                file_name = os.path.basename(opened_csv_file.name)
                storage.save(name=file_name, content=opened_csv_file)


def _get_storage_backend():
    """Return the storage backend (Object Store) specific for Datawarehouse.

    :returns: SwiftStorage instance
    """
    return SwiftStorage(
        api_auth_url=settings.DWH_SWIFT_AUTH_URL,
        api_username=settings.DWH_SWIFT_USERNAME,
        api_key=settings.DWH_SWIFT_PASSWORD,
        tenant_name=settings.DWH_SWIFT_TENANT_NAME,
        tenant_id=settings.DWH_SWIFT_TENANT_ID,
        region_name=settings.DWH_SWIFT_REGION_NAME,
        container_name=settings.DWH_SWIFT_CONTAINER_NAME)


def _create_signals_csv(location):
    """Create CSV file with all `Signal` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'signals.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            'id',
            'signal_uuid',
            'source',
            'text',
            'text_extra',
            'incident_date_start',
            'incident_date_end',
            'created_at',
            'updated_at',
            'operational_date',
            'expire_date',
            'image',
            'upload',
            'extra_properties',
            'category_id',
            'location_id',
            'reporter_id',
            'status_id',
        ])

        # Writing the header to the CSV file.

        # Writing all `Signal` objects to the CSV file.
        for signal in Signal.objects.all():
            writer.writerow([
                signal.pk,
                signal.signal_id,
                signal.source,
                signal.text,
                signal.text_extra,
                signal.incident_date_start,
                signal.incident_date_end,
                signal.created_at,
                signal.updated_at,
                signal.operational_date,
                signal.expire_date,
                signal.image,
                signal.upload,
                json.dumps(signal.extra_properties),
                signal.category_id,
                signal.location_id,
                signal.reporter_id,
                signal.status_id,
            ])

    return csv_file.name


def _create_locations_csv(location):
    """Create CSV file with all `Location` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'locations.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'lat',
            'lng',
            'stadsdeel',
            'buurt_code',
            'address',
            'address_text',
            'created_at',
            'updated_at',
            'extra_properties',
            '_signal_id',
        ])

        # Writing all `Location` objects to the CSV file.
        for location_obj in Location.objects.all():
            writer.writerow([
                location_obj.pk,
                location_obj.geometrie.x,
                location_obj.geometrie.y,
                location_obj.get_stadsdeel_display(),
                location_obj.buurt_code,
                json.dumps(location_obj.address),
                location_obj.address_text,
                location_obj.created_at,
                location_obj.updated_at,
                json.dumps(location_obj.extra_properties),
                location_obj._signal_id,
            ])

    return csv_file.name


def _create_reporters_csv(location):
    """Create CSV file with all `Reporter` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'reporters.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'email',
            'phone',
            'remove_at',
            'created_at',
            'updated_at',
            'extra_properties',
            '_signal_id',
        ])

        # Writing all `Reporter` objects to the CSV file.
        for reporter in Reporter.objects.all():
            writer.writerow([
                reporter.pk,
                reporter.email,
                reporter.phone,
                reporter.remove_at,
                reporter.created_at,
                reporter.updated_at,
                json.dumps(reporter.extra_properties),
                reporter._signal_id,
            ])

    return csv_file.name


def _create_categories_csv(location):
    """Create CSV file with all `Category` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'categories.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'main',
            'sub',
            'department',
            'priority',
            'ml_priority',
            'ml_cat',
            'ml_prob',
            'ml_cat_all',
            'ml_cat_all_prob',
            'ml_sub_cat',
            'ml_sub_prob',
            'ml_sub_all',
            'ml_sub_all_prob',
            'created_at',
            'updated_at',
            'extra_properties',
            '_signal_id',
        ])

        # Writing all `Category` objects to the CSV file.
        for category in Category.objects.all():
            writer.writerow([
                category.pk,
                category.main,
                category.sub,
                category.department,
                category.priority,
                category.ml_priority,
                category.ml_cat,
                category.ml_prob,
                category.ml_cat_all,
                category.ml_cat_all_prob,
                category.ml_sub_cat,
                category.ml_sub_prob,
                category.ml_sub_all,
                category.ml_sub_all_prob,
                category.created_at,
                category.updated_at,
                json.dumps(category.extra_properties),
                category._signal_id,
            ])

    return csv_file.name


def _create_statuses_csv(location):
    """Create CSV file with all `Status` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'statuses.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'text',
            'user',
            'target_api',
            'state_display',
            'extern',
            'created_at',
            'updated_at',
            'extra_properties',
            '_signal_id',
            'state',
        ])

        # Writing all `Status` objects to the CSV file.
        for status in Status.objects.all():
            writer.writerow([
                status.pk,
                status.text,
                status.user,
                status.target_api,
                status.get_state_display(),
                status.extern,
                status.created_at,
                status.updated_at,
                json.dumps(status.extra_properties),
                status._signal_id,
                status.state,
            ])

    return csv_file.name
