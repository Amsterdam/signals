import factory

from signals.apps.signals.models import Type


class TypeFactory(factory.DjangoModelFactory):
    _signal = factory.SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    name = Type.SIGNAL  # Default type is a "Signal" (Melding in Dutch)

    class Meta:
        model = Type
