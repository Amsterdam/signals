# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.test import TestCase

from signals.apps.questionnaires.factories import (
    AnswerFactory,
    QuestionFactory,
    QuestionnaireFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Answer, Question, Questionnaire, Session


class TestFactories(TestCase):
    def setUp(self):
        try:
            q = Question.objects.get_by_reference('submit')
        except Question.DoesNotExist:
            pass
        else:
            q.delete()

    def test_answer_factory(self):
        AnswerFactory.create()

        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(Questionnaire.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)

    def test_session_factory(self):
        SessionFactory.create()

        self.assertEqual(Answer.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(Questionnaire.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)

    def test_questionnaire_factory(self):
        QuestionnaireFactory.create()

        self.assertEqual(Answer.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
        self.assertEqual(Questionnaire.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)

    def test_question_factory(self):
        QuestionFactory.create()

        self.assertEqual(Answer.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
        self.assertEqual(Questionnaire.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 1)
