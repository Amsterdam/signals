from django.conf import settings
from django.core.management import BaseCommand

from signals.apps.search.documents.signal import SignalDocument


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            help='Delete all data in the elastic index')

    def handle(self, *args, **options):
        if not settings.FEATURE_FLAGS.get('SEARCH_BUILD_INDEX', False):
            self.stdout('elastic indexing disabled')
        else:
            self.stdout('elastic indexing')
            delete = options['delete']
            if delete:
                SignalDocument.clear_index()
            SignalDocument.index_documents()
        self.stdout('done!')
