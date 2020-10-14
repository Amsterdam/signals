import factory
from factory import fuzzy

from signals.apps.signals.models import Status
from signals.apps.signals.workflow import GEMELD


class StatusFactory(factory.DjangoModelFactory):

    class Meta:
        model = Status

    _signal = factory.SubFactory('tests.apps.signals.factories.signal.SignalFactory', status=None)

    text = fuzzy.FuzzyText(length=400)
    user = factory.Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    state = GEMELD  # Initial state is always 'm'
    extern = fuzzy.FuzzyChoice((True, False))

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
