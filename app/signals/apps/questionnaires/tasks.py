# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Vereniging van Nederlandse Gemeenten
from signals.apps.questionnaires.services.forward_to_external import clean_up_forward_to_external
from signals.apps.questionnaires.services.reaction_request import clean_up_reaction_request
from signals.celery import app


@app.task
def clean_up_reaction_request_task():
    clean_up_reaction_request()


@app.task
def clean_up_forward_to_external_task():
    clean_up_forward_to_external()
