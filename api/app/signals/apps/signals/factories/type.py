from factory import DjangoModelFactory, SubFactory

from signals.apps.signals.models import Type


class TypeFactory(DjangoModelFactory):
    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory')
    name = Type.SIGNAL  # Default type is a "Signal" (Melding in Dutch)

    class Meta:
        model = Type
