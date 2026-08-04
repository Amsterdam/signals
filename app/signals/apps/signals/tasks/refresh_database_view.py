# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
import logging

from django.db import connection

from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def refresh_materialized_view_public_signals_geography_feature_collection():
    """
    A task to refresh the materialized view that contains the data for the public/v1/signals/geography endpoint
    """
    refresh_query = 'REFRESH MATERIALIZED VIEW CONCURRENTLY "public_signals_geography_feature_collection";'

    cursor = connection.cursor()
    try:
        cursor.execute(refresh_query)
    except Exception as e:
        log.error(f'Failed to execute the query: {refresh_query}', exc_info=e)
    finally:
        cursor.close()
