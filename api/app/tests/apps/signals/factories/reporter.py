import string

import factory
from factory import fuzzy

from signals.apps.signals.models import Reporter


class ReporterFactory(factory.DjangoModelFactory):

    class Meta:
        model = Reporter

    _signal = factory.SubFactory('tests.apps.signals.factories.signal.SignalFactory', reporter=None)

    email = factory.Sequence(lambda n: 'veelmelder{}@example.com'.format(n))
    email_anonymized = False

    phone = fuzzy.FuzzyText(length=10, chars=string.digits)
    phone_anonymized = False

    @factory.post_generation
    def set_one_to_one_relation(self, create, extracted, **kwargs):
        self.signal = self._signal
