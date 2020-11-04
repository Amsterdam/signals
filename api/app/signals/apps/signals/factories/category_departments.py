from factory import DjangoModelFactory, SubFactory
from factory.fuzzy import FuzzyChoice

from signals.apps.signals.models import CategoryDepartment


class CategoryDepartmentFactory(DjangoModelFactory):
    class Meta:
        model = CategoryDepartment

    category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    department = SubFactory('signals.apps.signals.factories.department.DepartmentFactory')

    is_responsible = FuzzyChoice((True, False))
    can_view = FuzzyChoice((True, False))
