# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.questionnaires.models import Session
from signals.apps.questionnaires.services.reaction_request import ReactionRequestService
from signals.celery import app


@app.task
def update_status_reactie_ontvangen(pk):
    session = Session.objects.get(id=pk)
    ReactionRequestService.handle_frozen_session(session)
