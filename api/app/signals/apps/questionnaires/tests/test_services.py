# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.test import TestCase

from signals.apps.questionnaires.factories import QuestionFactory


def _question_graph_with_decision():
    q1 = QuestionFactory.create(key='q_yesno', payload={
        'shortLabel': 'Yes or no?',
        'label': 'Yes or no, what do you choose?',
        'next': [
            {'key': 'q_yes', 'answer': 'yes'},
            {'key': 'q_no', 'answer': 'no'},
        ],
    })

    q2 = QuestionFactory.create(key='q_yes', payload={
        'shortLabel': 'yes',
        'label': 'The yes question. Happy now?'
    })

    q3 = QuestionFactory.create(key='q_no', payload={
        'shortLabel': 'no',
        'label': 'The no question. Still unhappy?'
    })

    return q1, q2, q3


def _question_graph_with_decision_and_null_keys():
    q2 = QuestionFactory.create(key=None, payload={
        'shortLabel': 'yes',
        'label': 'The yes question. Happy now?'
    })

    q3 = QuestionFactory.create(key=None, payload={
        'shortLabel': 'no',
        'label': 'The no question. Still unhappy?'
    })

    q1 = QuestionFactory.create(key=None, payload={
        'shortLabel': 'Yes or no?',
        'label': 'Yes or no, what do you choose?',
        'next': [
            {'key': q2.key, 'answer': 'yes'},
            {'key': q3.key, 'answer': 'no'},
        ],
    })

    return q1, q2, q3


def _question_graph_with_cycle():
    q1 = QuestionFactory.create(key='one', payload={
        'shortLabel': 'First question.',
        'label': 'First question.',
        'next': [
            {'key': 'two'}
        ],
    })

    q2 = QuestionFactory.create(key='two', payload={
        'shortLabel': 'First question.',
        'label': 'First question.',
        'next': [
            {'key': 'one'}
        ],
    })

    return q1, q2


class TestQuestionGraphs(TestCase):
    def test_question_graph_with_decision(self):
        _question_graph_with_decision()
        _question_graph_with_decision_and_null_keys()
        _question_graph_with_cycle()


class TestAnswerService(TestCase):
    pass


class TestQuestionnaireService(TestCase):
    pass


class TestQuestionService(TestCase):
    pass


class TestSessionService(TestCase):
    pass
