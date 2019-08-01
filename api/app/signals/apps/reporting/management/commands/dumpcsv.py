from django.core.management import BaseCommand

from signals.apps.reporting.csv.datawarehouse import save_csv_files_datawarehouse


# TODO: Make per table dumps possible, default should dump all of it.
class Command(BaseCommand):
    def handle(self, *args, **options):
        save_csv_files_datawarehouse()
