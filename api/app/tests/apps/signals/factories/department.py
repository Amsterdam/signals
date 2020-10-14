import factory
from factory import fuzzy

from signals.apps.signals.models import Department


class DepartmentFactory(factory.DjangoModelFactory):
    code = fuzzy.FuzzyText(length=3)
    name = fuzzy.FuzzyText(length=10)
    is_intern = fuzzy.FuzzyChoice(choices=[True, False])
    can_direct = False

    class Meta:
        model = Department
