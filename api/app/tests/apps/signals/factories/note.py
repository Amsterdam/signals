import factory
from factory import fuzzy

from signals.apps.signals.models import Note


class NoteFactory(factory.DjangoModelFactory):
    text = fuzzy.FuzzyText(length=100)
    created_by = factory.Sequence(lambda n: 'ambtenaar{}@example.com'.format(n))
    _signal = factory.SubFactory('tests.apps.signals.factories.signal.SignalFactory')

    class Meta:
        model = Note
