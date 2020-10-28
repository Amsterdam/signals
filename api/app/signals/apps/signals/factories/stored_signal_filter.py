from factory import DjangoModelFactory, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import StoredSignalFilter


class StoredSignalFilterFactory(DjangoModelFactory):
    name = FuzzyText(length=100)
    created_by = SubFactory('signals.apps.users.factories.UserFactory')
    refresh = FuzzyChoice((True, False))

    class Meta:
        model = StoredSignalFilter
