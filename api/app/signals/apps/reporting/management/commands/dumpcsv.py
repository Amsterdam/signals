
from django.core.management import BaseCommand

from signals.apps.reporting.csv.datawarehouse import save_csv_files_datawarehouse

class Command(BaseCommand):
    def handle(self, *args, **options):
        save_csv_files_datawarehouse()
