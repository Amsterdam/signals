from factory import DjangoModelFactory, Sequence, SubFactory
from factory.fuzzy import FuzzyText

from signals.apps.signals.models import CategoryTranslation


class CategoryTranslationFactory(DjangoModelFactory):
    class Meta:
        model = CategoryTranslation

    created_by = Sequence(lambda n: 'beheerder{}@example.com'.format(n))
    text = FuzzyText(length=100)
    old_category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    new_category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
