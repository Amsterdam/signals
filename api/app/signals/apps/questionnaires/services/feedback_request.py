# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Support for Klanttevredenheidsonderzoek flow.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.feedback.utils import get_fe_application_location
from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import SessionNotFrozen, WrongFlow, WrongState
from signals.apps.questionnaires.models import (
    Choice,
    Edge,
    Question,
    QuestionGraph,
    Questionnaire,
    Session
)
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


def create_kto_graph():
    # First question, is reporter happy with resolution? Yes or no?
    q1 = Question.objects.create(
        analysis_key='satisfied',
        label='Bent u tevreden met de afhandeling van uw melding?',
        short_label='Tevreden',
        field_type='plain_text',
        enforce_choices=True,
        required=True,
    )
    c1_ja = Choice.objects.create(question=q1, payload='ja')
    c1_nee = Choice.objects.create(question=q1, payload='nee')
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
        field_type='plain_text',
        label='Mogen wij contact met u opnemen naar aanleiding van uw feedback?',
        short_label='Mogen wij contact met u opnemen naar aanleiding van uw feedback?',
        enforce_choices=True,
    )
    Choice.objects.create(question=q_allow_contact, payload='ja')
    Choice.objects.create(question=q_allow_contact, payload='nee')

    # Connect the questions to form a graph:
    Edge.objects.create(graph=graph, question=q1, next_question=q_satisfied, choice=c1_ja)
    Edge.objects.create(graph=graph, question=q1, next_question=q_unsatisfied, choice=c1_nee)
    Edge.objects.create(graph=graph, question=q_satisfied, next_question=q_extra_info, choice=None)
    Edge.objects.create(graph=graph, question=q_unsatisfied, next_question=q_extra_info, choice=None)
    Edge.objects.create(graph=graph, question=q_extra_info, next_question=q_allow_contact, choice=None)

    return graph


class FeedbackRequestService:
    @staticmethod
    def get_feedback_urls(session):
        fe_location = get_fe_application_location()
        positive_feedback_url = f'{fe_location}/feedback/ja/{session.uuid}'
        negative_feedback_url = f'{fe_location}/feedback/nee/{session.uuid}'

        return positive_feedback_url, negative_feedback_url

    @staticmethod
    def create_session(signal):
        if signal.status.state != workflow.AFGEHANDELD:
            msg = f'Signal {signal.id} is not in state REACTIE_GEVRAAGD!'
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

    @staticmethod
    def handle_frozen_session_FEEDBACK_REQUEST(session):
        from signals.apps.questionnaires.services import QuestionnairesService

        if not session.frozen:
            msg = f'Session {session.uuid} is not frozen!'
            raise SessionNotFrozen(msg)
        if session.questionnaire.flow != Questionnaire.FEEDBACK_REQUEST:
            msg = f'Questionnaire flow property for session {session.uuid} is not FEEDBACK_REQUEST!'
            raise WrongFlow(msg)

        # Collect information from the answers that were received and stored
        # on the Session instance.
        signal = session._signal
        QuestionnairesService.validate_session_using_question_graph(session)
        answers_by_analysis_key = QuestionnairesService.get_latest_answers_by_analysis_key(session)
        by_analysis_key = {k: a.payload for k, a in answers_by_analysis_key.items()}

        # Work around missing boolean FieldType
        satisfied = by_analysis_key['satisfied']
        is_satisfied = True if satisfied == 'ja' else False
        allows_contact = by_analysis_key.get('allows_contact', 'nee')
        allows_contact = True if allows_contact == 'ja' else False

        reason = by_analysis_key.get('reason_satisfied', None) or by_analysis_key.get('reason_unsatisfied', None)

        # Prepare a Feedback object, save it later
        feedback = Feedback(
            _signal=signal,
            created_at=session.created_at,
            submitted_at=timezone.now(),
            is_satisfied=is_satisfied,
            allows_contact=allows_contact,
            text=reason,
            text_extra=by_analysis_key.get('extra_info', None),
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
