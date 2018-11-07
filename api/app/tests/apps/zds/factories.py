import factory

from tests.apps.signals.factories import SignalFactory


class ZaakSignalFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.ZaakSignal"

    signal = factory.SubFactory(SignalFactory)
    zrc_link = 'http://amsterdam.nl/'


class ZaakDocumentFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.ZaakDocument"

    zaak_signal = factory.SubFactory(ZaakSignalFactory)
    drc_link = 'http://amsterdam.nl/'
