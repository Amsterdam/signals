# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Support for "reactie melder" flow.

This flow allows Signalen users to request extra information from a reporter
whose signal/complaint does not have all information that is required to handle
it. This assumes the reported signal/complaint was not anonymous, and that
an email address was available.

Current design only allows one question to be posed to the reporter.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils.timezone import now

from signals.apps.feedback.utils import get_fe_application_location
from signals.apps.questionnaires.app_settings import (
    NO_REACTION_RECEIVED_TEXT,
    REACTION_REQUEST_DAYS_OPEN
)
from signals.apps.questionnaires.exceptions import (
    CannotFreeze,
    SessionInvalidated,
    WrongFlow,
    WrongState
)
from signals.apps.questionnaires.models import Question, QuestionGraph, Questionnaire, Session
from signals.apps.questionnaires.services.session import SessionService
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal

logger = logging.getLogger(__name__)


def create_session_for_reaction_request(signal):
    """
    Prepare a Session to be answered by the original reporter.
    """
    if signal.status.state != workflow.REACTIE_GEVRAAGD:
        msg = f'Signal {signal.id} is not in state REACTIE_GEVRAAGD!'
        raise WrongState(msg)

    with transaction.atomic():
        question = Question.objects.create(
            required=True,
            field_type='plain_text',
            short_label='Reactie melder',
            label=signal.status.text,  # <-- this should not be empty, max 200 characters
            analysis_key='reaction',
        )
        graph = QuestionGraph.objects.create(first_question=question, name='Reactie gevraagd.')
        questionnaire = Questionnaire.objects.create(
            graph=graph,
            name='Reactie gevraagd',
            flow=Questionnaire.REACTION_REQUEST,
        )
        session = Session.objects.create(
            submit_before=now() + timedelta(days=REACTION_REQUEST_DAYS_OPEN),
            questionnaire=questionnaire,
            _signal=signal,
        )

    return session


def get_reaction_url(session):
    frontend_base_url = get_fe_application_location()
    return f'{frontend_base_url}/incident/reactie/{session.uuid}'


def clean_up_reaction_request():
    # Find all signals that have been in state REACTIE_GEVRAAGD for too
    # long and change their state to REACTIE_ONTVANGEN with a text saying
    # no reaction was received.
    signals = Signal.objects.filter(
        status__state=workflow.REACTIE_GEVRAAGD,
        status__created_at__lt=now() - timedelta(days=REACTION_REQUEST_DAYS_OPEN)
    )

    count = 0
    for signal in signals:
        payload = {'text': NO_REACTION_RECEIVED_TEXT, 'state': workflow.REACTIE_ONTVANGEN}
        Signal.actions.update_status(data=payload, signal=signal)
        count += 1

    return count


class ReactionRequestSessionService(SessionService):
    def is_publicly_accessible(self):
        """
        Is self.session accessible via public API (reaction request flow).
        """
        # Check general access rules.
        super().is_publicly_accessible()

        # Check rection request flow specific rules
        signal = self.session._signal

        # Check that a signal is associated with this session
        if signal is None:
            msg = f'Session {self.session.uuid} is not associated with a Signal.'
            logger.warning(msg, stack_info=True)
            raise SessionInvalidated(msg)

        # Make sure that the signal is in state REACTIE_GEVRAAGD.
        if signal.status.state != workflow.REACTIE_GEVRAAGD:
            msg = f'Session {self.session.uuid} is invalidated, associated signal not in state REACTIE_GEVRAAGD.'
            logger.warning(msg, stack_info=True)
            raise SessionInvalidated(msg)

        # Make sure that only the most recent Session and associated
        # Questionnaire and Question can be answered:
        most_recent_session = Session.objects.filter(
            _signal=signal, questionnaire__flow=Questionnaire.REACTION_REQUEST).order_by('created_at').last()
        if most_recent_session.uuid != self.session.uuid:
            msg = f'Session {self.session.uuid} is invalidated, a newer reaction request was issued.'
            raise SessionInvalidated(msg)

    def freeze(self, refresh=True):
        """
        Freeze self.session, apply reaction request business rules.
        """
        if refresh:
            self.load_data()  # Make sure cache is not stale // TODO: this can raise, deal with it

        if not self.can_freeze:
            msg = f'Session (uuid={self.session.uuid}) is not fully answered.'
            raise CannotFreeze(msg)

        if self.session.questionnaire.flow != Questionnaire.REACTION_REQUEST:
            msg = f'Questionnaire flow property for session {self.session.uuid} is not REACTION_REQUEST!'
            raise WrongFlow(msg)

        super().freeze()

        answers = self.get_answers_by_analysis_key()
        answer = answers['reaction']

        Signal.actions.update_status(
            {'text': answer.payload, 'state': workflow.REACTIE_ONTVANGEN}, self.session._signal)
