# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2025 Gemeente Amsterdam
from signals.apps.classification.train import TrainClassifier
from signals.celery import app


@app.task
def train_classifier(training_set_ids, use_signals_in_database_for_training):
    TrainClassifier(training_set_ids, use_signals_in_database_for_training).run()
