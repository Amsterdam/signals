import factory
from django.utils import timezone
from factory import fuzzy

from signals.apps.feedback.models import Feedback, StandardAnswer

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


class StandardAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StandardAnswer

    text = factory.Sequence(lambda n: 'Unieke klaag tekst nummer: {}'.format(n))
    is_visible = fuzzy.FuzzyChoice([True, False])
    is_satisfied = fuzzy.FuzzyChoice([True, False])


class FeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feedback

    _signal = factory.SubFactory('tests.apps.signals.factories.SignalFactory')
    created_at = factory.LazyFunction(timezone.now)
    submitted_at = None

    is_satisfied = fuzzy.FuzzyChoice([True, False])
    allows_contact = fuzzy.FuzzyChoice([True, False])
    text = factory.Sequence(lambda n: 'Unieke klaag tekst nummer: {}'.format(n))
    text_extra = fuzzy.FuzzyChoice([None, 'Daarom is waarom.'])
