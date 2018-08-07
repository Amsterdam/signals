import csv
import tempfile
import os

from django.core.files.storage import default_storage

from signals.models import Signal


def create_signals_csv(location_dir):
    """Create CSV file with all `Signal` objects.

    :param location_dir: Path to location dir
    :returns: Path to CSV file
    """
    with open(os.path.join(location_dir, 'signals.csv'), 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Writing the header to the CSV file.
        writer.writerow([
            'id',
            'signal_id',
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
                signal.extra_properties,
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
