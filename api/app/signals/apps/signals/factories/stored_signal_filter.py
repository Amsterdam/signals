import factory
from factory import fuzzy

from signals.apps.signals.models import StoredSignalFilter


class StoredSignalFilterFactory(factory.DjangoModelFactory):
    name = fuzzy.FuzzyText(length=100)

    class Meta:
        model = StoredSignalFilter
