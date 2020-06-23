"""
Dump CSV of SIA tables matchting the old, agreed-upon, format.
"""
# Implements fix for SIG-1456.
import csv
import json
import logging
import os
import tempfile
from pprint import pprint

from django.conf import settings
from django.db import connection, reset_queries

from signals.apps.feedback.models import Feedback
from signals.apps.reporting.app_settings import CSV_BATCH_SIZE as BATCH_SIZE
from signals.apps.reporting.csv.utils import _get_storage_backend
from signals.apps.signals.models import (
    Category,
    CategoryAssignment,
    Location,
    Reporter,
    ServiceLevelObjective,
    Signal,
    Status
)

logger = logging.getLogger(__name__)


def get_swift_parameters():
    """Get Swift parameters for Datawarehouse"""
    return {
        'api_auth_url': settings.DWH_SWIFT_AUTH_URL,
        'api_username': settings.DWH_SWIFT_USERNAME,
        'api_key': settings.DWH_SWIFT_PASSWORD,
        'tenant_name': settings.DWH_SWIFT_TENANT_NAME,
        'tenant_id': settings.DWH_SWIFT_TENANT_ID,
        'region_name': settings.DWH_SWIFT_REGION_NAME,
        'container_name': settings.DWH_SWIFT_CONTAINER_NAME,
        'auto_overwrite': True,
    }


# TODO: make it possible to save to local disk.
def save_csv_files_datawarehouse():
    """Create CSV files for Datawarehouse and save them on the storage backend.

    :returns:
    """
    # Creating all CSV files.
    csv_files = list()
    with tempfile.TemporaryDirectory() as tmp_dir:
        reset_queries()
        csv_files.append(_create_signals_csv(tmp_dir))
        csv_files.append(_create_locations_csv(tmp_dir))
        csv_files.append(_create_reporters_csv(tmp_dir))
        csv_files.append(_create_category_assignments_csv(tmp_dir))
        csv_files.append(_create_statuses_csv(tmp_dir))
        csv_files.append(_create_category_sla_csv(tmp_dir))

        # KTO feedback if running on acceptance or production
        try:
            csv_files.append(_create_kto_feedback_csv(tmp_dir))
        except EnvironmentError:
            pass

        pprint(connection.queries)
        # Getting the storage backend and save all CSV files.
        storage = _get_storage_backend(get_swift_parameters())
        for csv_file_path in csv_files:
            with open(csv_file_path, 'rb') as opened_csv_file:
                file_name = os.path.basename(opened_csv_file.name)
                storage.save(name=file_name, content=opened_csv_file)


def _create_signals_csv(location):
    """Create CSV file with all `Signal` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'signals.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
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
            'category_assignment_id',
            'location_id',
            'reporter_id',
            'status_id',

            # SIG-2823
            'priority',
            'priority_created_at',
            'parent',
            'type',
            'type_created_at',
        ])

        # Writing all `Signal` objects to the CSV file.
        qs = Signal.objects.all()

        for signal in qs.iterator(chunk_size=BATCH_SIZE):
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
                # signal.image,  # <- causes n+1, disabled for now
                '',
                signal.upload,
                json.dumps(signal.extra_properties),
                signal.category_assignment_id,
                signal.location_id,
                signal.reporter_id,
                signal.status_id,

                # SIG-2823
                signal.priority.priority if signal.priority else '',
                signal.priority.created_at if signal.priority else '',
                signal.parent_id if signal.is_child() else '',
                signal.type_assignment.name if signal.type_assignment else '',
                signal.type_assignment.created_at if signal.type_assignment else '',
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
        qs = Location.objects.order_by('id').all()
        for location_obj in qs.iterator(chunk_size=BATCH_SIZE):
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
            'is_anonymized',
            'created_at',
            'updated_at',
            'extra_properties',
            '_signal_id',
        ])

        # Writing all `Reporter` objects to the CSV file.
        qs = Reporter.objects.all()

        for reporter in qs.iterator(chunk_size=BATCH_SIZE):
            writer.writerow([
                reporter.pk,
                reporter.email,
                reporter.phone,
                reporter.is_anonymized,
                reporter.created_at,
                reporter.updated_at,
                None,  # always empty
                reporter._signal_id,
            ])

    return csv_file.name


def _create_category_assignments_csv(location):
    """Create CSV file with all `CategoryAssignment` objects.

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
            'departments',
            'created_at',
            'updated_at',
            'extra_properties',
            '_signal_id',
        ])

        departments_cache = {
            c.id: ', '.join(
                [d.name for d in c.departments.filter(categorydepartment__is_responsible=True)]
            ) for c in Category.objects.prefetch_related('departments').all()
        }

        # Writing all `CategoryAssignment` objects to the CSV file.
        qs = CategoryAssignment.objects.select_related('category', 'category__parent')\
            .order_by('id').all()

        for category_assignment in qs.iterator(chunk_size=BATCH_SIZE):
            writer.writerow([
                category_assignment.pk,
                category_assignment.category.parent.name,
                category_assignment.category.name,
                departments_cache[category_assignment.category_id],
                category_assignment.created_at,
                category_assignment.updated_at,
                json.dumps(category_assignment.extra_properties),
                category_assignment._signal_id,
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
        qs = Status.objects.all()
        for status in qs.iterator(chunk_size=BATCH_SIZE):
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


def _create_kto_feedback_csv(location):
    """Create a CSV file with all `Feedback` objects."""

    environment = os.getenv('ENVIRONMENT')

    if environment is None:
        raise EnvironmentError('ENVIRONMENT env variable not set')
    elif environment.upper() not in ['PRODUCTION', 'ACCEPTANCE']:
        raise EnvironmentError('ENVIRONMENT env variable is wrong {}'.format(environment))

    file_name = f'kto-feedback-{environment}.csv'

    with open(os.path.join(location, file_name), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # header
        writer.writerow([
            '_signal_id',
            'is_satisfied',
            'allows_contact',
            'text',
            'text_extra',
            'created_at',
            'submitted_at',
        ])

        # instances
        qs = Feedback.objects.filter(submitted_at__isnull=False)
        for feedback in qs.iterator(chunk_size=BATCH_SIZE):
            writer.writerow([
                feedback._signal_id,
                feedback.is_satisfied,
                feedback.allows_contact,
                feedback.text,
                feedback.text_extra,
                feedback.created_at,
                feedback.submitted_at,
            ])

    return csv_file.name


def _create_category_sla_csv(location):
    """Create CSV file with all `ServiceLevelObjective` objects.

    :param location: Directory for saving the CSV file
    :returns: Path to CSV file
    """
    with open(os.path.join(location, 'sla.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'main',
            'sub',
            'n_days',
            'use_calendar_days',
            'created_at'
        ])

        # Writing all `ServiceLevelObjective` objects to the CSV file.
        qs = ServiceLevelObjective.objects.select_related(
            'category',
            'category__parent'
        ).order_by(
            'category_id',
            '-created_at'
        )

        for slo in qs.iterator(chunk_size=BATCH_SIZE):
            writer.writerow([
                slo.pk,
                slo.category.parent.name,
                slo.category.name,
                slo.n_days,
                slo.use_calendar_days,
                slo.created_at
            ])

    return csv_file.name
