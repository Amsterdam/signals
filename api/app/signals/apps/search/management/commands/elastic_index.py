from django.core.management import BaseCommand

from signals.apps.search.documents.signal import SignalDocument


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            help='Delete all data in the elastic index')

    def handle(self, *args, **options):
        self.stdout.write('elastic indexing')
        delete = options['delete']
        if delete:
            SignalDocument.clear_index()
        SignalDocument.index_documents()
        self.stdout.write('done!')
