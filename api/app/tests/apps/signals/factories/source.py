import factory

from signals.apps.signals.models import Source


class SourceFactory(factory.DjangoModelFactory):
    class Meta:
        model = Source

    name = factory.Sequence(lambda n: f'Bron {n}')
    description = factory.Sequence(lambda n: f'Beschrijving bron {n}')
