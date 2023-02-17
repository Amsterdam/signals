# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Support for Klanttevredenheidsonderzoek flow.
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import CannotFreeze, WrongFlow, WrongState
from signals.apps.questionnaires.models import (
    Choice,
    Edge,
    Question,
    QuestionGraph,
    Questionnaire,
    Session
)
from signals.apps.questionnaires.services.session import SessionService
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


def create_kto_graph():
    # First question, is reporter happy with resolution? Yes or no?
    q1 = Question.objects.create(
        analysis_key='satisfied',
        label='Bent u tevreden met de afhandeling van uw melding?',
        short_label='Tevreden',
        field_type='boolean',
        enforce_choices=True,
        required=True,
    )
    c1_ja = Choice.objects.create(question=q1, payload=True, display='Ja, ik ben tevreden.')
    c1_nee = Choice.objects.create(question=q1, payload=False, display='Nee, ik ben niet tevreden.')
    graph = QuestionGraph.objects.create(first_question=q1)

    # Question for satisfied reporter
    q_satisfied = Question.objects.create(
        analysis_key='reason_satisfied',
        label='Waarom bent u tevreden?',
        short_label='Waarom bent u tevreden?',
        field_type='plain_text',
        required=False,
    )
    reasons_satisfied = StandardAnswer.objects.filter(is_visible=True, is_satisfied=True)
    for reason in reasons_satisfied:
        Choice.objects.create(question=q_satisfied, payload=reason.text)

    # Question for unsatisfied reporter
    q_unsatisfied = Question.objects.create(
        analysis_key='reason_unsatisfied',
        label='Waarom bent u ontevreden?',
        short_label='Waarom bent u ontevreden?',
        field_type='plain_text',
        required=False,
    )
    reasons_unsatisfied = StandardAnswer.objects.filter(is_visible=True, is_satisfied=False)
    for reason in reasons_unsatisfied.all():
        Choice.objects.create(question=q_unsatisfied, payload=reason.text)

    # Now some general questions
    q_extra_info = Question.objects.create(
        analysis_key='extra_info',
        field_type='plain_text',
        label='Wilt u verder nog iets vermelden of toelichten?',
        short_label='Wilt u verder nog iets vermelden of toelichten?',
        required=False,
    )
    q_allow_contact = Question.objects.create(
        analysis_key='allows_contact',
        field_type='boolean',
        label='Mogen wij contact met u opnemen naar aanleiding van uw feedback?',
        short_label='Mogen wij contact met u opnemen naar aanleiding van uw feedback?',
        enforce_choices=True,
    )
    Choice.objects.create(question=q_allow_contact, payload=True, display='Ja')
    Choice.objects.create(question=q_allow_contact, payload=False, display='Nee')

    # Connect the questions to form a graph:
    Edge.objects.create(graph=graph, question=q1, next_question=q_satisfied, choice=c1_ja)
    Edge.objects.create(graph=graph, question=q1, next_question=q_unsatisfied, choice=c1_nee)
    Edge.objects.create(graph=graph, question=q_satisfied, next_question=q_extra_info, choice=None)
    Edge.objects.create(graph=graph, question=q_unsatisfied, next_question=q_extra_info, choice=None)
    Edge.objects.create(graph=graph, question=q_extra_info, next_question=q_allow_contact, choice=None)

    return graph


def get_feedback_urls(session):
    positive_feedback_url = f'{settings.FRONTEND_URL}/feedback/ja/{session.uuid}'
    negative_feedback_url = f'{settings.FRONTEND_URL}/feedback/nee/{session.uuid}'

    return positive_feedback_url, negative_feedback_url


def create_session_for_feedback_request(signal):
    if signal.status.state != workflow.AFGEHANDELD:
        msg = f'Signal {signal.id} is not in state AFGEHANDELD!'
        raise WrongState(msg)

    with transaction.atomic():
        graph = create_kto_graph()
        questionnaire = Questionnaire.objects.create(graph=graph, flow=Questionnaire.FEEDBACK_REQUEST)
        session = Session.objects.create(
            submit_before=timezone.now() + timedelta(days=FEEDBACK_REQUEST_DAYS_OPEN),
            questionnaire=questionnaire,
            _signal=signal,
        )

    return session


class FeedbackRequestSessionService(SessionService):
    def freeze(self, refresh=True):  # noqa: C901
        """
        Freeze self.session, apply feedback request business rules.
        """

        signal = self.session._signal

        if refresh:
            self.refresh_from_db()  # Make sure cache is not stale // TODO: this can raise, deal with it

        if not self._can_freeze:
            msg = f'Session (uuid={self.session.uuid}) is not fully answered.'
            raise CannotFreeze(msg)

        if self.session.questionnaire.flow != Questionnaire.FEEDBACK_REQUEST:
            msg = f'Questionnaire flow property for session {self.session.uuid} is not REACTION_REQUEST!'
            raise WrongFlow(msg)

        super().freeze()

        answers_by_analysis_key = self.answers_by_analysis_key
        payload_by_analysis_key = {k: a.payload for k, a in answers_by_analysis_key.items()}

        is_satisfied = payload_by_analysis_key['satisfied']
        reason = payload_by_analysis_key.get('reason_satisfied', None) or \
            payload_by_analysis_key.get('reason_unsatisfied', None)

        # Prepare a Feedback object, save it later
        feedback = Feedback(
            _signal=signal,
            created_at=self.session.created_at,
            submitted_at=timezone.now(),
            is_satisfied=is_satisfied,
            allows_contact=payload_by_analysis_key.get('allows_contact', False),
            text=reason,
            text_extra=payload_by_analysis_key.get('extra_info', None),
        )

        # We check whether the reason given (when unsatisfied) is one that
        # requires the complaints/signal to be reopened.
        if is_satisfied:
            reopen = False
        else:
            try:
                sa = StandardAnswer.objects.get(text=reason)
            except StandardAnswer.DoesNotExist:
                reopen = True
            else:
                if not sa.is_satisfied:
                    reopen = sa.reopens_when_unhappy

        with transaction.atomic():
            if reopen and signal.status.state == workflow.AFGEHANDELD:
                payload = {
                    'text': 'De melder is niet tevreden blijkt uit feedback. Zo nodig heropenen.',
                    'state': workflow.VERZOEK_TOT_HEROPENEN,
                }
                Signal.actions.update_status(payload, signal)
            feedback.save()
