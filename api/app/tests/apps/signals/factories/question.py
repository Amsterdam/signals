import factory
from factory import fuzzy

from signals.apps.signals.models import Question


class QuestionFactory(factory.DjangoModelFactory):
    key = fuzzy.FuzzyText(length=3)
    field_type = fuzzy.FuzzyChoice(choices=list(dict(Question.FIELD_TYPE_CHOICES).keys()))
    meta = '{ "dummy" : "test" }'
    required = fuzzy.FuzzyChoice(choices=[True, False])

    class Meta:
        model = Question
