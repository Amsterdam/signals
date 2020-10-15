import factory

from signals.apps.signals.models import CategoryAssignment


class CategoryAssignmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = CategoryAssignment

    _signal = factory.SubFactory('tests.apps.signals.factories.signal.SignalFactory', category_assignment=None)
    category = factory.SubFactory('tests.apps.signals.factories.category.CategoryFactory')

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
