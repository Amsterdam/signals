# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from factory import LazyFunction, SelfAttribute, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory
from faker import Faker

from signals.apps.questionnaires.models import (
    ActionTrigger,
    Answer,
    Choice,
    Edge,
    InfoTrigger,
    Question,
    QuestionGraph,
    Questionnaire,
    Session
)

fake = Faker()


class QuestionFactory(DjangoModelFactory):
    key = Sequence(lambda n: f'question-{n}')
    # Note we only create plain_text questions in this factory, with no
    # next question reference present. Tests that need those will have to
    # create model instances themselves.
    field_type = 'plain_text'
    label = Sequence(lambda n:  f'Long label for question {n}.')
    short_label = Sequence(lambda n: f'Short label for question {n}.')

    required = True

    class Meta:
        model = Question


class QuestionGraphFactory(DjangoModelFactory):
    name = Sequence(lambda n: f'Question Graph {n}')
    first_question = SubFactory(QuestionFactory)

    class Meta:
        model = QuestionGraph


class EdgeFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)
    question = SubFactory(QuestionFactory)
    next_question = SubFactory(QuestionFactory)

    class Meta:
        model = Edge


class ActionTriggerFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)
    question = SubFactory(QuestionFactory)

    class Meta:
        model = ActionTrigger


class InfoTriggerFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)
    question = SubFactory(QuestionFactory)

    class Meta:
        model = InfoTrigger


class ChoiceFactory(DjangoModelFactory):
    question = SubFactory(QuestionFactory)

    class Meta:
        model = Choice


class QuestionnaireFactory(DjangoModelFactory):
    graph = SubFactory(QuestionGraphFactory)

    flow = Questionnaire.EXTRA_PROPERTIES

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
        if not obj.payload:
            obj.payload = f'Answer to: {obj.question.short_label}.'

    class Meta:
        model = Answer
