# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from signals.apps.questionnaires.models import Session
from signals.apps.questionnaires.models.questionnaire import Questionnaire
from signals.apps.questionnaires.services import (
    FeedbackRequestSessionService,
    ReactionRequestSessionService,
    SessionService
)

SESSION_SERVICE_FOR_FLOW = {
    Questionnaire.REACTION_REQUEST: ReactionRequestSessionService,
    Questionnaire.FEEDBACK_REQUEST: FeedbackRequestSessionService,
}


def get_session_service(session_uuid):
    """
    Get correct SessionService subclass for a given session UUID.
    """
    session = Session.objects.get(uuid=session_uuid)

    if not session.questionnaire:
        raise Exception(f'Session (uuid={str(session_uuid)}) has no associated questionnaire.')

    cls = SESSION_SERVICE_FOR_FLOW.get(session.questionnaire.flow, SessionService)
    return cls(session)
