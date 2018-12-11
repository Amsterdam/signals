import factory

from tests.apps.signals.factories import SignalFactory


class CaseSignalFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.CaseSignal"

    signal = factory.SubFactory(SignalFactory)
    zrc_link = 'http://amsterdam.nl/'


class CaseDocumentFactory(factory.DjangoModelFactory):

    class Meta:
        model = "zds.CaseDocument"

    case_signal = factory.SubFactory(CaseSignalFactory)
    drc_link = 'http://amsterdam.nl/'
