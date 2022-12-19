# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import logging
from datetime import timedelta

from signals.apps.gisib.data_loaders.quercus_tree_loader import QuercusTreeLoader
from signals.celery import app

logger = logging.getLogger(__name__)


@app.task
def load_quercus_trees(days=None, purge_table=False):
    time_delta = timedelta(days=days) if days else None
    QuercusTreeLoader().load(time_delta=time_delta, purge_table=purge_table)
