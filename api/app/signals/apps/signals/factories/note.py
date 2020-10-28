from factory import DjangoModelFactory, Sequence, SubFactory
from factory.fuzzy import FuzzyText

from signals.apps.signals.models import Note


class NoteFactory(DjangoModelFactory):
    text = FuzzyText(length=100)
    created_by = Sequence(lambda n: 'ambtenaar{}@example.com'.format(n))
    _signal = SubFactory('signals.apps.signals.factories.signal.SignalFactory')

    class Meta:
        model = Note
