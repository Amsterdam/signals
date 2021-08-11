# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Support for Klanttevredenheidsonderzoek flow.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from signals.apps.feedback.utils import get_fe_application_location
from signals.apps.feedback.models import StandardAnswer, Feedback
from signals.apps.questionnaires.app_settings import FEEDBACK_REQUEST_DAYS_OPEN
from signals.apps.questionnaires.exceptions import SessionNotFrozen, WrongFlow, WrongState
from signals.apps.questionnaires.models import Choice, Edge, Question, Questionnaire, QuestionGraph, Session, Trigger
from signals.apps.signals import workflow


def create_kto_graph():
    # First question, is reporter happy with resolution? Yes or no?
    q1 = Question.objects.create(
        key='satisfied',
        label='Bent u tevreden met de afhandeling van uw melding?',
        short_label='Tevreden',
        field_type='plain_text',
        enforce_choices=False,
        required=True,
    )
    c1_ja = Choice.objects.create(question=q1, payload='ja')
    c1_nee = Choice.objects.create(question=q1, payload='nee')
    graph = QuestionGraph.objects.create(first_question=q1)  # Create our QuestionGraph here, triggers need it.

    # Question for satisfied reporter
    q_satisfied = Question.objects.create(
        key='reason_satisfied',
        label='Waarom bent u tevreden?',
        short_label='Waarom bent u tevreden?',
        field_type='plain_text',

    )
    reasons_satisfied = StandardAnswer.objects.filter(is_visible=True, is_satisfied=True)
    for reason in reasons_satisfied:
        Choice.objects.create(question=q_satisfied, payload=reason.text)

    # Question for unsatisfied reporter
    q_unsatisfied = Question.objects.create(
        key='reason_unsatisfied',
        label='Waarom bent u ontevreden?',
        short_label='Waarom bent u ontevreden?',
        field_type='plain_text',
    )
    reasons_unsatisfied = StandardAnswer.objects.filter(is_visible=True, is_satisfied=False)
    for reason in reasons_unsatisfied.all():
        Choice.objects.create(question=q_unsatisfied, payload=reason.text)

        if reason.reopens_when_unhappy:
            Trigger.objects.create(graph=graph, question=reasons_unsatisfied, payload=reason.text)

    # Now some general questions
    q_extra_info = Question.objects.create(
        key='extra_info',
        field_type='plain_text',
        label='Wilt u verder nog iets vermelden of toelichten?',
        short_label='Wilt u verder nog iets vermelden of toelichten?',
    )
    q_allow_contact = Question.objects.create(
        key='allow_contact',
        field_type='plain_text',
        label='Mogen wij contact met u opnemen naar aanleiding van uw feedback?',
        short_label='Mogen wij contact met u opnemen naar aanleiding van uw feedback?',
    )

    # Connect the questions to form a graph:
    Edge.objects.create(graph=graph, question=q1, next_question=q_satisfied, payload=c1_ja.payload)
    Edge.objects.create(graph=graph, question=q1, next_question=q_unsatisfied, payload=c1_nee.payload)
    Edge.objects.create(graph=graph, question=q_satisfied, next_question=q_extra_info)
    Edge.objects.create(graph=graph, question=q_unsatisfied, next_question=q_extra_info)
    Edge.objects.create(graph=graph, question=q_extra_info, next_question=q_allow_contact)

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
            questionnaire = Questionnaire.objects.create(
                graph=graph,
            )
            session = Session.objects.create(
                submit_before=timezone.now() + timedelta(days=FEEDBACK_REQUEST_DAYS_OPEN),
                questionnaire=questionnaire,
                _signal=signal,
            )

        return session
