from timeit import default_timer as timer

from django.core.management import BaseCommand
from django.utils import timezone

from signals.apps.search.documents.signal import SignalDocument
from signals.apps.signals.models import Signal


class Command(BaseCommand):
    _dry_run = False

    def add_arguments(self, parser):
        parser.add_argument('-c', '--clear-index', action='store_true', dest='_clear_index', help='Clear the index')
        parser.add_argument('-d', '--delete', action='store_true', dest='_clear_index', help='Delete the index, deprecated use --clear-index instead')  # noqa
        parser.add_argument('--dry-run', action='store_true', dest='_dry_run', help='Dry-run mode')
        parser.add_argument('--index-all', action='store_true', dest='_index_documents', help='Index all Signals')
        parser.add_argument('--init', action='store_true', dest='_init_index', help='Init the index')
        parser.add_argument('--signal-id', type=str, dest='signal_id', help='A specific signal that need re-indexing')
        parser.add_argument('--signal-ids', type=str, dest='signal_ids', help='A set of signals that need re-indexing')
        parser.add_argument('--from-date', type=str, dest='from_date', help='Index all signals from date, format YYYY-MM-DD')  # noqa
        parser.add_argument('--to-date', type=str, dest='to_date', help='Index all signals from date, format YYYY-MM-DD')  # noqa

    def handle(self, *args, **options):
        start = timer()
        self.stdout.write('Elastic management command')

        ping = True if self._dry_run else SignalDocument.ping()
        if not ping:
            self.stderr.write('* Elastic cluster not online!')
        else:
            self._apply_options(**options)

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')

    def _apply_options(self, **options):
        self._dry_run = options['_dry_run']
        if self._dry_run:
            self.stdout.write('* Dry Run enabled, no changes will be made to the index')

        if options['_clear_index']:
            self._clear_index()

        if options['_init_index'] and not options['_clear_index']:
            self._init_index()

        if options['signal_id']:
            self._index_signal(signal_id=int(options['signal_id']))
        elif options['signal_ids']:
            self._index_signals(signal_ids=list(map(int, options['signal_ids'].split(','))))
        elif options['from_date'] or options['to_date']:
            from_date = options['from_date'] or None
            to_date = options['to_date'] or None
            self._index_date_range(from_date, to_date)
        elif options['_index_documents']:
            self._index_documents()
        else:
            self.stdout.write('* No index option given')

    def _clear_index(self):
        self.stdout.write('* Clear the index')
        if not self._dry_run:
            SignalDocument.clear_index()
            self._init_index()

    def _init_index(self):
        self.stdout.write('* Init the index')
        if not self._dry_run:
            SignalDocument.init()

    def _index_documents(self):
        self.stdout.write('* Index all Signals in bulk')
        if not self._dry_run:
            SignalDocument.index_documents()

    def _index_signal(self, signal_id):
        self.stdout.write(f'* Index Signal #{signal_id}')

        try:
            signal = Signal.objects.get(pk=signal_id)
        except Signal.DoesNotExist:
            self.stderr.write(f'* Signal #{signal_id} does not exists')
            return None

        if not self._dry_run:
            SignalDocument.init()
            signal_document = SignalDocument.create_document(signal)
            signal_document.save()

    def _index_signals(self, signal_ids):
        self.stdout.write(f'* Indexing Signals: #{", #".join(map(str, signal_ids))}')

        signal_qs = Signal.objects.filter(id__in=signal_ids).order_by('-updated_at')
        signal_qs_ids = signal_qs.values_list('id', flat=True)
        ids_diff = set(signal_ids) - set(signal_qs_ids)
        if ids_diff:
            self.stderr.write(f'* Signals not found #{", #".join(map(str, ids_diff))}')
        else:
            if not self._dry_run:
                SignalDocument.index_documents(queryset=signal_qs)

    def _index_date_range(self, from_date=None, to_date=None):
        if not from_date and not to_date:
            self.stderr.write('* At least a from date or a to date needs to be specified')
            return

        if from_date:
            from_date = timezone.make_aware(timezone.datetime.strptime(from_date, '%Y-%m-%d'))
        else:
            from_date = timezone.now()
        from_date = from_date.replace(hour=00, minute=00, second=00)  # Beginning of the given day

        if to_date:
            to_date = timezone.make_aware(timezone.datetime.strptime(to_date, '%Y-%m-%d'))
        else:
            to_date = timezone.now()
        to_date = to_date.replace(hour=23, minute=59, second=59)  # End of the given day

        if to_date < from_date:
            self.stderr.write('* To date cannot be before the from date')
            return

        signal_qs = Signal.objects.filter(updated_at__range=[from_date, to_date]).order_by('-updated_at')
        self.stdout.write(f'* Indexing Signals in range from {from_date:%Y-%m-%d %H:%M:%S} to '
                          f'{to_date:%Y-%m-%d %H:%M:%S}, found {signal_qs.count()} signals')
        if not self._dry_run:
            SignalDocument.index_documents(queryset=signal_qs)
