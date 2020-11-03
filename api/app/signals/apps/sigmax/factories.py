import factory
from django.utils import timezone
from factory import fuzzy

from signals.apps.sigmax.models import CityControlRoundtrip


class CityControlRoundtripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CityControlRoundtrip

    _signal = factory.SubFactory('signals.apps.signals.factories.SignalFactory')
    when = fuzzy.FuzzyDateTime(timezone.now())
