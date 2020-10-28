import factory

from signals.apps.signals.models import Priority


class PriorityFactory(factory.DjangoModelFactory):

    class Meta:
        model = Priority

    _signal = factory.SubFactory('signals.apps.signals.factories.signal.SignalFactory', priority=None)

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
