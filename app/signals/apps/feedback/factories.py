# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2023 Gemeente Amsterdam
import factory
from django.utils import timezone
from factory import fuzzy

from signals.apps.feedback.models import Feedback, StandardAnswer, StandardAnswerTopic

REASONS = [
    'Wind uit het oosten.',
    'Met het verkeerde been uit bed.',
    'Het regent.',
    'De zon schijnt.',
    'Het is maandag.',
    'Het is weekend.',
    'Dit jaargetijde',
    'Ik ben chagrijnig.',
    'Ik ben vrolijk.',
]


class StandardAnswerTopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StandardAnswerTopic
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: 'topic name: {}'.format(n))
    description = factory.Sequence(lambda n: 'topic text: {}'.format(n))
    order: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([0, 1, 2, 3, 4, 5])


class StandardAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StandardAnswer
        skip_postgeneration_save = True

    text = factory.Sequence(lambda n: 'Unieke klaag tekst nummer: {}'.format(n))
    is_visible: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([True, False])
    is_satisfied: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([True, False])
    topic: factory.SubFactory = factory.SubFactory(StandardAnswerTopicFactory)
    order: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([0, 1, 2, 3, 4, 5])


class FeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feedback
        skip_postgeneration_save = True

    _signal: factory.SubFactory = factory.SubFactory('signals.apps.signals.factories.SignalFactory')
    created_at = factory.LazyFunction(timezone.now)
    submitted_at = None

    is_satisfied: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([True, False])
    allows_contact: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([True, False])
