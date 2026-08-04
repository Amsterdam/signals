# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging

from django.db import connection

from signals.celery import app

log = logging.getLogger(__name__)

VIEW_NAME = 'public_signals_geography_feature_collection'


@app.task
def refresh_materialized_view_public_signals_geography_feature_collection():
    """
    A task to refresh the materialized view that contains the data for the public/v1/signals/geography endpoint
    """
    refresh_query = f'REFRESH MATERIALIZED VIEW CONCURRENTLY "{VIEW_NAME}";'

    cursor = connection.cursor()
    try:
        # A materialized view that has never been populated, which is how pg_dump writes it out and thus how it
        # ends up in an environment that was restored from a dump, cannot be refreshed CONCURRENTLY. That first
        # refresh has to be the blocking variant, it takes an ACCESS EXCLUSIVE lock on the view.
        cursor.execute("SELECT relispopulated FROM pg_class WHERE relkind = 'm' AND relname = %s", [VIEW_NAME])
        row = cursor.fetchone()
        if row and not row[0]:
            log.warning(f'Materialized view "{VIEW_NAME}" is not populated, refreshing without CONCURRENTLY')
            refresh_query = f'REFRESH MATERIALIZED VIEW "{VIEW_NAME}";'

        cursor.execute(refresh_query)
    except Exception as e:
        log.error(f'Failed to execute the query: {refresh_query}', exc_info=e)
    finally:
        cursor.close()
