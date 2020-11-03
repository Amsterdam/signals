from factory import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from signals.apps.signals.models import Department


class DepartmentFactory(DjangoModelFactory):
    code = FuzzyText(length=3)
    name = FuzzyText(length=10)
    is_intern = FuzzyChoice(choices=[True, False])
    can_direct = False

    class Meta:
        model = Department
