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
from datetime import timedelta

from django.db import transaction
from django.utils.timezone import now

from signals.apps.feedback.utils import get_fe_application_location
from signals.apps.questionnaires.app_settings import (
    NO_REACTION_RECEIVED_TEXT,
    REACTION_REQUEST_DAYS_OPEN
)
from signals.apps.questionnaires.exceptions import SessionNotFrozen, WrongFlow, WrongState
from signals.apps.questionnaires.models import Answer, Question, Questionnaire, Session
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class ReactionRequestService:
    @staticmethod
    def get_reaction_url(session):
        frontend_base_url = get_fe_application_location()
        return f'{frontend_base_url}/incident/reactie/{session.uuid}'

    @staticmethod
    def create_session(signal):
        if signal.status.state != workflow.REACTIE_GEVRAAGD:
            msg = f'Signal {signal.id} is not in state REACTIE_GEVRAAGD!'
            raise WrongState(msg)

        with transaction.atomic():
            question = Question.objects.create(
                required=True,
                field_type='plain_text',
                short_label='Reactie melder',
                label=signal.status.text,  # <-- this should not be empty, max 200 characters
            )
            questionnaire = Questionnaire.objects.create(
                first_question=question,
                name='Reactie gevraagd',
                flow=Questionnaire.REACTION_REQUEST,
            )
            session = Session.objects.create(
                submit_before=now() + timedelta(days=REACTION_REQUEST_DAYS_OPEN),
                questionnaire=questionnaire,
                _signal=signal,
            )

        return session

    @staticmethod
    def handle_frozen_session_REACTION_REQUEST(session):
        if not session.frozen:
            msg = f'Session {session.uuid} is not frozen!'
            raise SessionNotFrozen(msg)
        if session.questionnaire.flow != Questionnaire.REACTION_REQUEST:
            msg = f'Questionnaire flow property for session {session.uuid} is not REACTION_REQUEST!'
            raise WrongFlow(msg)

        signal = session._signal
        question = session.questionnaire.first_question
        answer = Answer.objects.filter(session=session, question=question).order_by('-created_at').first()

        Signal.actions.update_status({'text': answer.payload, 'state': workflow.REACTIE_ONTVANGEN}, signal)

    @staticmethod
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
