import random

import factory
from factory import fuzzy

from signals.apps.signals.models import StatusMessageTemplate
from signals.apps.signals.workflow import STATUS_CHOICES_API


class StatusMessageTemplateFactory(factory.DjangoModelFactory):
    title = fuzzy.FuzzyText(length=100)
    text = fuzzy.FuzzyText(length=100)
    order = 0
    category = factory.SubFactory('signals.apps.signals.factories.category.CategoryFactory')
    state = factory.LazyAttribute(lambda o: random.choice(STATUS_CHOICES_API)[0])

    class Meta:
        model = StatusMessageTemplate
