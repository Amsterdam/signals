# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from signals.apps.questionnaires.models import Edge, Question, QuestionGraph, Questionnaire, Session
from signals.apps.questionnaires.services import QuestionnairesService


class QuestionnairesProxyService:
    @staticmethod
    def get_or_create_questionnaire():
        question_is_satisfied, _ = Question.objects.get_or_create(
            key='Feedback proxy question',
            defaults=dict(
                label='Feedback proxy question',
                short_label='Feedback proxy question',
                field_type='plain_text',
                required=True,
            )
        )
        question_allows_contact, _ = Question.objects.get_or_create(
            key='Feedback proxy allows contact',
            defaults=dict(
                label='Feedback proxy allows contact',
                short_label='Feedback proxy allows contact',
                field_type='plain_text',
                required=True,
            )
        )
        graph, _ = QuestionGraph.objects.get_or_create(
            name='Feedback proxy graph',
            defaults=dict(
                first_question=question_is_satisfied,
            )
        )
        Edge.objects.get_or_create(
            graph=graph,
            question=question_is_satisfied,
            next_question=question_allows_contact,
        )
        questionnaire, _ = Questionnaire.objects.get_or_create(
            name='Feedback proxy questionnaire',
            graph=graph,
            flow=Questionnaire.FEEDBACK_REQUEST,
            is_active=True,
            defaults=dict(
                description='Feedback proxy questionnaire',
            )
        )

        return questionnaire

    @staticmethod
    def create_session(signal):
        questionnaire = QuestionnairesProxyService.get_or_create_questionnaire()
        session = QuestionnairesService.create_session(questionnaire, duration=timedelta(weeks=1))

        session._signal_id = signal.pk
        session.save()

        return session

    @staticmethod
    def answer_feedback_session(feedback, validated_data):
        try:
            session = Session.objects.get(uuid=feedback.token, _signal_id=feedback._signal_id)
        except Session.DoesNotExist:
            return
        else:
            QuestionnairesService.create_answer(
                answer_payload=validated_data['text'] or validated_data['text_extra'],
                question=Question.objects.get(key='Feedback proxy question'),
                questionnaire=session.questionnaire,
                session=session
            )

            QuestionnairesService.create_answer(
                answer_payload=str(validated_data['allows_contact']),
                question=Question.objects.get(key='Feedback proxy allows contact'),
                questionnaire=session.questionnaire,
                session=session
            )

            return QuestionnairesService.freeze_session(session)
