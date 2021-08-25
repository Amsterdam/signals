# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """
    !!! USE FOR DEVELOPMENT ONLY FOR NOW !!!

    This command copies the signal_history_view database view into the history_log table.
    It can sync the whole view or just 1 Signal.

    TODO: Make this management command more robust so that it can run on ACC and PROD
    """
    _dry_run = False

    def add_arguments(self, parser):
        parser.add_argument('--signal-id', type=str, dest='signal_id', help='The ID of a specific signal')
        parser.add_argument('--dry-run', action='store_true', dest='_dry_run', help='Dry-run mode')

    def handle(self, *args, **options):
        self._dry_run = options['_dry_run']
        if self._dry_run:
            self.stdout.write('* [dry-run] enabled')

            # Only show the outcome of the query instead of inserting data
            if options['signal_id']:
                self.stdout.write(f'* [dry-run] Insert for Signal #{options["signal_id"]}')
                query = self._select_where(signal_id=int(options['signal_id']))
            else:
                self.stdout.write('* [dry-run] Insert for all Signals')
                query = self._select_query()
        else:
            # Insert the actual data
            if options['signal_id']:
                self.stdout.write(f'* Insert for Signal #{options["signal_id"]}')
                query = self._insert_query(signal_id=int(options['signal_id']))
            else:
                self.stdout.write('* Insert for all Signals')
                query = self._insert_query()

        if query:
            self._execute_query(query=query)

    def _execute_query(self, query):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            if self._dry_run:
                self.stdout.write(f'* [dry-run] query: {query}')
                for row in cursor.fetchall():
                    self.stdout.write(f'* [dry-run] {", ".join([str(col) for col in row])}')
        except Exception as e:
            self.stdout.write(f'* Error executing query: {e}')
        finally:
            cursor.close

    def _select_where(self, signal_id):
        select_where_query = f'{self._select_query()} WHERE shv._signal_id = {signal_id}'
        return select_where_query

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
        """
        return select_query

    def _insert_query(self, signal_id=None):
        insert_query = f'INSERT INTO history_log (content_type_id, object_pk, action, description, extra, created_by, created_at, _signal_id)'  # noqa

        if signal_id:
            insert_query = f'{insert_query} {self._select_where(signal_id=signal_id)}'
        else:
            insert_query = f'{insert_query} {self._select_query()}'
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

        insert_content_type_case = f'{insert_content_type_case} ELSE 0 END'
        return insert_content_type_case
