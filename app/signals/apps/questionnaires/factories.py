# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2023 Gemeente Amsterdam
from factory import LazyFunction, SelfAttribute, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from signals.apps.questionnaires.models import (
    Answer,
    Choice,
    Edge,
    Question,
    QuestionGraph,
    Questionnaire,
    Session,
    Trigger
)

fake = Faker()


class QuestionFactory(DjangoModelFactory):
    retrieval_key = Sequence(lambda n: f'question-{n}')
    analysis_key = Sequence(lambda n: f'analysis-key-for-question-{n}')
    # Note we only create plain_text questions in this factory, with no
    # next question reference present. Tests that need those will have to
    # create model instances themselves.
    field_type = 'plain_text'
    label = Sequence(lambda n:  f'Long label for question {n}.')
    short_label = Sequence(lambda n: f'Short label for question {n}.')

    required = True

    class Meta:
        model = Question
        skip_postgeneration_save = True


class QuestionGraphFactory(DjangoModelFactory):
    name = Sequence(lambda n: f'Question Graph {n}')
    first_question = SubFactory(QuestionFactory)

    class Meta:
        model = QuestionGraph
        skip_postgeneration_save = True


class ChoiceFactory(DjangoModelFactory):
    question = SubFactory(QuestionFactory)

    class Meta:
        model = Choice
        skip_postgeneration_save = True


class EdgeFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)
    question = SubFactory(QuestionFactory)
    next_question = SubFactory(QuestionFactory)
    choice = SubFactory(ChoiceFactory)

    class Meta:
        model = Edge
        skip_postgeneration_save = True


class TriggerFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)
    question = SubFactory(QuestionFactory)

    class Meta:
        model = Trigger
        skip_postgeneration_save = True


class QuestionnaireFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)

    flow = Questionnaire.EXTRA_PROPERTIES

    name = LazyFunction(fake.sentence)
    description = LazyFunction(fake.paragraph)
    is_active = True

    class Meta:
        model = Questionnaire
        skip_postgeneration_save = True


class SessionFactory(DjangoModelFactory):
    started_at = None  # session is not yet active
    submit_before = None  # session has no submission deadline

    questionnaire = SubFactory(QuestionnaireFactory)

    class Meta:
        model = Session
        skip_postgeneration_save = True


class AnswerFactory(DjangoModelFactory):
    session = SubFactory(SessionFactory)
    question = SelfAttribute('session.questionnaire.first_question')
    payload = None

    class Meta:
        model = Answer
        skip_postgeneration_save = True
