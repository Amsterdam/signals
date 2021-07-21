# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.test import TestCase

from signals.apps.questionnaires.factories import QuestionFactory
from signals.apps.questionnaires.models import Question


class TestQuestionManager(TestCase):
    def setUp(self):
        self.question = QuestionFactory.create()

    def test_get_by_reference_key(self):
        q = Question.objects.get_by_reference(self.question.key)
        self.assertEqual(q.key, self.question.key)

    def test_get_by_reference_uuid(self):
        q = Question.objects.get_by_reference(str(self.question.uuid))
        self.assertEqual(q.uuid, self.question.uuid)

    def test_get_by_reference_submit(self):
        # Remove submit question from database, check that a question is
        # returned when using the appropriate manager method.
        try:
            q = Question.objects.get(key='submit')
        except Question.DoesNotExist:
            pass
        else:
            q.delete()

        self.assertEqual(Question.objects.count(), 1)
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(key='submit')

        q = Question.objects.get_by_reference('submit')
        self.assertEqual(q.key, 'submit')
