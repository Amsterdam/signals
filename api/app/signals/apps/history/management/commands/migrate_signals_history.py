# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    _dry_run = False

    def add_arguments(self, parser):
        parser.add_argument('--signal-id', type=str, dest='signal_id', help='The ID of a specific signal')
        parser.add_argument('--dry-run', action='store_true', dest='_dry_run', help='Dry-run mode')
        parser.add_argument('--from', type=str, dest='from', help='History logged after date (YYYY-MM-DD)')
        parser.add_argument('--to', type=str, dest='to', help='History logged before date (YYYY-MM-DD)')

    def handle(self, *args, **options):
        self.stdout.write(f'* Migrate history')

        self._dry_run = options['_dry_run']
        self.stdout.write(f'* [dry-run] mode: {"on" if self._dry_run else "off"}')

        self.from_date = None
        if options['from']:
            self.from_date = timezone.datetime.strptime(options['from'], '%Y-%m-%d')
            self.stdout.write(f'* from: {self.from_date}')

        self.to_date = None
        if options['to']:
            self.to_date = timezone.datetime.strptime(options['to'], '%Y-%m-%d')
            self.stdout.write(f'* to: {self.to_date}')

        self.signal_id = None
        if options['signal_id']:
            self.signal_id = int(options['signal_id'])
            self.stdout.write(f'* signal_id: {self.signal_id}')

        if self._dry_run:
            query = self._select_query()
        else:
            query = self._insert_query()

        if query:
            self._execute_query(query=query)

    def _execute_query(self, query):
        cursor = connection.cursor()
        try:
            if self._dry_run:
                self.stdout.write(f'* [dry-run] query: {query}')
            else:
                cursor.execute(query)
                self.stdout.write(f'* inserted rows: {cursor.rowcount}')
        except Exception as e:
            self.stdout.write(f'* Error executing query: {e}')
        finally:
            cursor.close

    def _select_query(self):
        select_query = f"""
            SELECT
               {self._query_case()} AS content_type_id,
               reverse(substr(reverse(shv.identifier), 0, strpos(reverse(shv.identifier), '_')))::text as object_pk,
               substr(shv.what, 0, strpos(shv.what, '_')) as action,
               shv.description,
               shv.extra,
               shv.who as created_by,
               shv."when" as created_at,
               shv._signal_id as _signal_id
            FROM signals_history_view AS shv
            LEFT JOIN history_log hl on shv._signal_id = hl._signal_id and shv.when = hl.created_at
            WHERE hl._signal_id IS NULL
        """

        if self.from_date:
            select_query = f'{select_query} AND shv."when" >= \'{self.from_date}\''

        if self.to_date:
            select_query = f'{select_query} AND shv."when" <= \'{self.to_date}\''

        if self.signal_id:
            select_query = f'{select_query} AND shv._signal_id = {self.signal_id}'

        return select_query

    def _insert_query(self):
        insert_query = 'INSERT INTO history_log ' \
                       '(content_type_id, object_pk, action, description, extra, created_by, created_at, _signal_id) ' \
                       f'{self._select_query()}'
        return insert_query

    def _query_case(self):
        insert_content_type_case = 'CASE'

        content_types = ContentType.objects.filter(model__in=['location', 'feedback', 'note', 'type', 'status',
                                                              'categoryassignment', 'priority', 'servicelevelobjective',
                                                              'signaluser', ])

        ct_translations = {'categoryassignment': 'category_assignment',
                           'servicelevelobjective': 'sla',
                           'type': 'type_assignment',
                           'signal_user': 'signaluser', }
        for content_type in content_types:
            ct_pk = content_type.pk
            ct_name = ct_translations[content_type.model] if content_type.model in ct_translations else content_type.model  # noqa
            insert_content_type_case = f'{insert_content_type_case} WHEN lower(substr(shv.what, strpos(shv.what, \'_\')+1)) = \'{ct_name}\' THEN {ct_pk}'  # noqa

        content_type = ContentType.objects.get(model='signaldepartments')
        insert_content_type_case = f'{insert_content_type_case} WHEN lower(substr(shv.what, strpos(shv.what, \'_\')+1)) = \'routing_assignment_\' THEN {content_type.pk}'  # noqa
        insert_content_type_case = f'{insert_content_type_case} WHEN lower(substr(shv.what, strpos(shv.what, \'_\')+1)) = \'directing_departments_assignment\' THEN {content_type.pk}'  # noqa

        content_type = ContentType.objects.get(model='signal')
        insert_content_type_case = f'{insert_content_type_case} WHEN lower(shv.what) = \'child_signal_created\' THEN {content_type.pk}'  # noqa

        insert_content_type_case = f'{insert_content_type_case} ELSE 0 END'
        return insert_content_type_case
