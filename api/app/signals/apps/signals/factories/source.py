from factory import DjangoModelFactory, Sequence

from signals.apps.signals.models import Source


class SourceFactory(DjangoModelFactory):
    class Meta:
        model = Source

    name = Sequence(lambda n: f'Bron {n}')
    description = Sequence(lambda n: f'Beschrijving bron {n}')
