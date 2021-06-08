# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from factory import LazyFunction, SelfAttribute, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory
from faker import Faker

from signals.apps.questionnaires.models import Answer, Question, Questionnaire, Session

fake = Faker()


class QuestionFactory(DjangoModelFactory):
    key = Sequence(lambda n: f'question-{n}')
    # Note we only create plain_text questions in this factory, with no
    # next question reference present. Tests that need those will have to
    # create model instances themselves.
    field_type = 'plain_text'
    payload = Sequence(lambda n: {
        'shortLabel': f'Short label for question {n}.',
        'label': f'Long label for question {n}.',
    })
    required = True

    class Meta:
        model = Question


class QuestionnaireFactory(DjangoModelFactory):
    first_question = SubFactory(QuestionFactory)

    name = LazyFunction(fake.sentence)
    description = LazyFunction(fake.paragraph)
    is_active = True

    class Meta:
        model = Questionnaire


class SessionFactory(DjangoModelFactory):
    started_at = None  # session is not yet active
    submit_before = None  # session has no submission deadline

    questionnaire = SubFactory(QuestionnaireFactory)

    class Meta:
        model = Session


class AnswerFactory(DjangoModelFactory):
    session = SubFactory(SessionFactory)
    question = SelfAttribute('session.questionnaire.first_question')
    payload = None

    @post_generation
    def set_question_and_answer(obj, create, extracted, **kwargs):
        obj.payload = f'Answer to: {obj.question.payload["shortLabel"]}.'

    class Meta:
        model = Answer
