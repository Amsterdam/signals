import factory
from faker import Faker
from factory import fuzzy, SubFactory
from signals.apps.automation.models import ForwardToExternal, SetState
from signals.apps.signals import workflow

fake = Faker()

class ForwardToExternalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ForwardToExternal
        skip_postgeneration_save = True

    expression: SubFactory = SubFactory('signals.apps.signals.factories.expression.ExpressionFactory')
    email: str = fake.email()
    text: str = fake.text()

class SetStateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SetState
        skip_postgeneration_save = True

    expression: SubFactory = SubFactory('signals.apps.signals.factories.expression.ExpressionFactory')
    desired_state: fuzzy.FuzzyChoice = fuzzy.FuzzyChoice([workflow.AFGEHANDELD, workflow.GEANNULEERD])
    text: str = fake.text()

