import csv
import tempfile
import os
import json

from django.core.files.storage import default_storage

from signals.models import Signal, Location, Reporter


def create_signals_csv(directory):
    """Create CSV file with all `Signal` objects.

    :param directory: Path to dir for saving the CSV filea
    :returns: Path to CSV file
    """
    with open(os.path.join(directory, 'signals.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'signal_uuid',
            'source',
            'text',
            'text_extra',
            'location_id',
            'status_id',
            'category_id',
            'reporter_id',
            'incident_date_start',
            'incident_date_end',
            'created_at',
            'updated_at',
            'operational_date',
            'expire_date',
            'image',
            'upload',
            'extra_properties',
        ])

        # Writing all `Signal` objects to the CSV file.
        for signal in Signal.objects.all():
            writer.writerow([
                signal.pk,
                signal.signal_id,
                signal.source,
                signal.text,
                signal.text_extra,
                signal.location_id,
                signal.status_id,
                signal.category_id,
                signal.reporter_id,
                signal.incident_date_start,
                signal.incident_date_end,
                signal.created_at,
                signal.updated_at,
                signal.operational_date,
                signal.expire_date,
                signal.image,
                signal.upload,
                json.dumps(signal.extra_properties),
            ])

    return csv_file.name


def create_locations_csv(directory):
    """Create CSV file with all `Location` objects.

    :param directory: Path to dir for saving the CSV filea
    :returns: Path to CSV file
    """
    with open(os.path.join(directory, 'locations.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            '_signal_id',
            'lat',
            'lng',
            'stadsdeel',
            'buurt_code',
            'address',
            'address_text',
            'created_at',
            'updated_at',
            'extra_properties',
        ])

        # Writing all `Location` objects to the CSV file.
        for signal in Location.objects.all():
            writer.writerow([
                signal.pk,
                signal._signal_id,
                signal.geometrie.x,
                signal.geometrie.y,
                signal.get_stadsdeel_display(),
                signal.buurt_code,
                json.dumps(signal.address),
                signal.address_text,
                signal.created_at,
                signal.updated_at,
                json.dumps(signal.extra_properties),
            ])

    return csv_file.name


def create_reporters_csv(directory):
    """Create CSV file with all `Reporter` objects.

    :param directory: Path to dir for saving the CSV filea
    :returns: Path to CSV file
    """
    with open(os.path.join(directory, 'reporters.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            '_signal_id',
            'email',
            'phone',
            'remove_at',
            'created_at',
            'updated_at',
            'extra_properties',
        ])

        # Writing all `Reporter` objects to the CSV file.
        for signal in Reporter.objects.all():
            writer.writerow([
                signal.pk,
                signal._signal_id,
                signal.email,
                signal.phone,
                signal.remove_at,
                signal.created_at,
                signal.updated_at,
                json.dumps(signal.extra_properties),
            ])

    return csv_file.name


def save_csv_to_object_store(csv_file):
    """Save given CSV file to objectstore.

    :param csv_file:
    :returns:
    """
    # default_storage =
    pass


def handle():
    tmp_dir = tempfile.mkdtemp()
    signals_csv_file = create_signals_csv(tmp_dir)
    save_csv_to_object_store(signals_csv_file)
