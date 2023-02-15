# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
import logging

from signals.apps.questionnaires.models import Session
from signals.apps.questionnaires.models.questionnaire import Questionnaire
from signals.apps.questionnaires.services import (
    FeedbackRequestSessionService,
    ForwardToExternalSessionService,
    ReactionRequestSessionService,
    SessionService
)

logger = logging.getLogger(__name__)

SESSION_SERVICE_FOR_FLOW = {
    Questionnaire.REACTION_REQUEST: ReactionRequestSessionService,
    Questionnaire.FEEDBACK_REQUEST: FeedbackRequestSessionService,
    Questionnaire.EXTRA_PROPERTIES: SessionService,
    Questionnaire.FORWARD_TO_EXTERNAL: ForwardToExternalSessionService,
}


def get_session_service(session):
    """
    Get correct SessionService subclass for Session or session UUID.
    """
    if isinstance(session, Session):
        session.refresh_from_db()
    else:
        session = Session.objects.get(uuid=session)

    if not session.questionnaire:
        raise Exception(f'Session (uuid={str(session)}) has no associated questionnaire.')

    try:
        cls = SESSION_SERVICE_FOR_FLOW[session.questionnaire.flow]
    except KeyError:
        msg = f'Falling back to basic SessionService for session (UUID={session.uuid}).'
        logger.warning(msg)

    return cls(session)
