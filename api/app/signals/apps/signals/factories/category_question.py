from factory import DjangoModelFactory, Sequence, SubFactory

from signals.apps.signals.models import CategoryQuestion


class CategoryQuestionFactory(DjangoModelFactory):
    class Meta:
        model = CategoryQuestion

    category = SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    question = SubFactory('signals.apps.signals.factories.question.QuestionFactory')
    order = Sequence(lambda n: n)
